import os
import pathlib
import re
import subprocess
import sys
import textwrap


from . import log
from . import s3path


import boto3


PATH_RE = re.compile(r'(?<!s3:)/+')


def execute_command(command):
    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        encoding='utf-8'
    )
    if p.returncode != 0:
        log.render(log.ftext(f'error: failed to run command: {command}', c='red'))
        log.render(log.ftext(f'stdout: {p.stdout}', c='red'))
        log.render(log.ftext(f'stderr: {p.stderr}', c='red'))
        sys.exit(1)
    return p


def join_paths(*paths):
    return PATH_RE.sub('/', '/'.join(paths))


def process_input_directories(run_dir, run):
    paths_s3_info = list()
    paths_local = list()
    for dirpath in run_dir:
        if dirpath.startswith('s3'):
            if re_result := s3path.S3_PATH_RE.match(dirpath):
                paths_s3_info.append({
                    'bucket': re_result.group(1),
                    'key': re_result.group(2),
                })
            else:
                assert False
        else:
            paths_local.append(pathlib.Path(dirpath))
    # Process paths
    # NOTE: this should be done after AWS config check
    if paths_s3_info:
        if not s3path.MESSAGE_LOGGED:
            log.render('Retrieving S3 path file list, this may take some time')
            s3path.MESSAGE_LOGGED = True
        paths_s3 = s3path.process_paths(paths_s3_info, run)
    else:
        paths_s3 = list()
    return [*paths_s3, *paths_local]


def get_bucket_and_key(full_path):
    if re_result := s3path.S3_PATH_RE.match(full_path):
        bucket_name = re_result.group(1)
        key_prefix = re_result.group(2)
    else:
        assert False
    return bucket_name, key_prefix


def upload_log_and_config(log_fp, nextflow_dir, output_remote_dir):
    upload_log(log_fp, output_remote_dir)
    upload_nextflow_dir(nextflow_dir, output_remote_dir)


def upload_nextflow_dir(nextflow_dir, output_remote_dir):
    bucket_name, key_prefix = get_bucket_and_key(output_remote_dir)
    s3_bucket = boto3.resource('s3').Bucket(bucket_name)
    for fp_local in nextflow_dir.rglob('*'):
        if fp_local.is_dir():
            continue
        fp_local_str = str(fp_local)
        fp_local_rel = fp_local_str.replace(str(nextflow_dir.parent), '')
        fp_remote = join_paths(key_prefix, fp_local_rel)
        s3_bucket.upload_file(fp_local_str, fp_remote)


def upload_log(log_fp, output_remote_dir):
    bucket_name, key_prefix = get_bucket_and_key(output_remote_dir)
    nextflow_remote_dir = join_paths(output_remote_dir, log_fp.name)
    fp_remote = join_paths(key_prefix, log_fp.name)
    boto3.resource('s3').Bucket(bucket_name).upload_file(str(log_fp), fp_remote)


def regex_glob(regex, dirpath, data_source=None):
    matches = [dirpath]
    matches_new = list()
    for regex_part in regex.split('/'):
        while matches:
            # Only allow files to be matches on final iteration
            filepath = matches.pop()
            if not filepath.is_dir():
                continue
            for entry in filepath_iterator(filepath):
                entry_str = get_filepath_str(entry)
                if re.search(regex_part, entry_str):
                    matches_new.append(entry)
        matches = matches_new
        matches_new = list()
    if len(matches) > 1:
        if data_source == 'tumour-ensemble':
            match_selected = sorted(matches, key=get_filepath_str)[0]
            msg = textwrap.dedent(f'''
                warning: got {len(matches)} tumour samples for {dirpath} but we currently only
                support single tumour samples. Selecting the first sample for comparison:
                {match_selected}.
            ''').strip().replace('\n', '')
            log.render(log.ftext(msg, c='yellow'))
            log.render_newline()
            matches = [match_selected]
        else:
            log.render(log.ftext(f"error: ambiguous match with '{regex}' in {dirpath}:", c='red'))
            for match in matches:
                log.render(log.ftext(f'\t{str(match)}', c='red'))
            sys.exit(1)
    return matches


def filepath_iterator(filepath):
    if isinstance(filepath, s3path.VirtualPath):
        yield from filepath.iterdir()
    else:
        yield from os.scandir(filepath)


def get_filepath_str(filepath):
    if isinstance(filepath, s3path.VirtualPath):
        # s3path.VirtualPath currently distinguishes directories and files by trailing
        # slash. DirEntry.path will always return string paths without trailing slashes.
        # For consistent behaviour, we remove VirtualPath trailing slashes.
        return re.sub('/$', '', str(filepath))
    else:
        return filepath.path
