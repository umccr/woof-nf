import argparse
import datetime
import os
import pathlib
import re
import sys
import tempfile
import textwrap


from . import log
from . import s3path


PATH_RE = re.compile(r'(?<!s3:)//')


def join_paths(*paths):
    return PATH_RE.sub('/', '/'.join(paths))


def collect() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--run_dir_one',
        required=True,
        nargs='+',
        help='Space separated list of run directories'
    )
    parser.add_argument(
        '--run_dir_two',
        required=True,
        nargs='+',
        help='Space separated list of run directories'
    )
    parser.add_argument(
        '--output_dir',
        required=True,
        type=str,
        help='Output directory'
    )
    parser.add_argument(
        '--log_fp',
        type=str,
        help='Log filepath (default: <output_dir>/pipeline_log.txt)'
    )
    parser.add_argument(
        '--executor',
        choices=('local', 'aws'),
        default='local',
        help='Workflow executor (default: local)'
    )
    parser.add_argument(
        '--work_dir',
        help='Nextflow work directory (default: <args.output_dir>/nextflow/work/)'
    )
    parser.add_argument(
        '--docker',
        action='store_true',
        help='Force use of docker with local executor'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume previous workflow'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force configuration'
    )
    return parser.parse_args()


def check_and_process(args: argparse.Namespace) -> argparse.Namespace:
    log.task_msg_title('Checking and processing arguments')
    log.render_newline()

    # Cast inputs to pathlib.Path or as s3path.VirtualPath
    args.run_dir_one = process_input_directories(args.run_dir_one, run='one')
    args.run_dir_two = process_input_directories(args.run_dir_two, run='two')

    # TODO: refuse to run locally with S3 inputs without --force
    #           - must first deal with S3 input path handling...
    #           - once that is clear how it will be dealt with, then implement this

    # Set output mode, create local execution directory if we're send output to S3
    # args.output_dir: always local
    # args.output_remote_dir: S3 path for AWS execution
    args.output_remote_dir = None
    if str(args.output_dir).startswith('s3://'):
        args.output_type = 's3'
        args.output_remote_dir = args.output_dir
        args.output_dir = tempfile.mkdtemp(prefix='nf_', dir=pathlib.Path.cwd())
    else:
        args.output_type = 'local'
    args.output_dir = pathlib.Path(args.output_dir)

    # Set appropriate work directory, disallow some configs
    args.nextflow_dir = args.output_dir / 'nextflow'
    if args.executor == 'aws':
        if not args.work_dir:
            args.work_dir = join_paths(args.output_remote_dir, 'work')
        elif not args.work_dir.startswith('s3://'):
            msg = textwrap.dedent('''
                AWS job execution requires S3 work directory, remove --work-dir or manually set
                to S3 path
            ''').strip().replace('\n', '')
            log.render(log.ftext(f'error: {msg}', c='red'))
            sys.exit(1)
    elif args.executor == 'local' and not args.work_dir:
        args.work_dir = args.nextflow_dir / 'work'

    if args.work_dir.startswith('s3://') and not args.output_type == 's3':
        msg = 'refusing to use a S3 work directory with local output'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)

    if args.output_type == 's3' and not args.executor == 'aws':
        msg = textwrap.dedent('''
            refusing to run locally and then upload files to S3, change --output_dir to a local
            directory or set --executor to as 'aws'
        ''').strip().replace('\n', ' ')
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)

    if args.output_type == 'local' and args.executor == 'aws' and not args.force:
        msg = 'refusing to run on AWS and output locally without --force'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)

    if args.executor == 'aws' and not args.docker:
        log.render('info: aws executor requires docker but wasn\'t explicitly set, forcing')
        args.docker = True

    # Create local output directories
    if args.output_type == 'local' and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)
    if args.output_type == 'local' and not os.path.exists(args.nextflow_dir):
        os.makedirs(args.nextflow_dir, exist_ok=True)

    # Set up log file
    # args.log_fp: always local
    # args.log_remote_fp: S3 path; only allowed with remote output
    args.run_timestamp = '{:%Y%m%d_%H%M%S}'.format(datetime.datetime.now())
    log_fn = f'pipeline_log_{args.run_timestamp}.txt'
    if not args.log_fp:
        args.log_fp = pathlib.Path(args.output_dir, log_fn)
    elif args.log_fp.startswith('s3://'):
        if not args.output_type == 's3':
            msg = 'refusing to write log to S3 when writing output locally'
            log.render(log.ftext(f'error: {msg}', c='red'))
            sys.exit(1)
        args.log_remote_fp = args.log_fp
        args.log_fp = pathlib.Path(args.output_dir, log_fn)

    if not args.log_fp.parent.exists():
        msg = f'--log_fp parent directory does not exist: {args.log_fp.parent}'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)
    return args


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
