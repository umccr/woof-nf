import re


from . import s3path


import boto3


PATH_RE = re.compile(r'(?<!s3:)/+')


def join_paths(*paths):
    return PATH_RE.sub('/', '/'.join(paths))


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
