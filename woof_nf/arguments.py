import argparse
import multiprocessing
import pathlib
import re
import sys


from . import log
from . import s3path


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
        type=pathlib.Path,
        help='Output directory'
    )
    parser.add_argument(
        '--log_fp',
        type=pathlib.Path,
        help='Log filepath (default: <output_dir>/pipeline_log.txt)'
    )
    parser.add_argument(
        '--executor',
        choices=('local', 'aws'),
        default='local',
        help='Workflow executor (default: local)'
    )
    parser.add_argument(
        '--s3_bucket',
        help='S3 bucket for temporary file store when using the AWS executor'
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
    return parser.parse_args()


def check_and_process(args: argparse.Namespace) -> argparse.Namespace:
    log.task_msg_title('Checking and processing arguments')
    log.render_newline()
    # Cast inputs to pathlib.Path or as s3path.VirtualPath
    args.run_dir_one = process_input_directories(args.run_dir_one, run='one')
    args.run_dir_two = process_input_directories(args.run_dir_two, run='two')
    # Create output directory if it does not already exist
    if not args.output_dir.exists():
        args.output_dir.mkdir(parents=True, exist_ok=True)
    # Set default log filepath if none set, otherwise ensure parent of set path does exist
    if args.log_fp == None:
        args.log_fp = args.output_dir / 'pipeline_log.txt'
        log.setup_log_file(args.log_fp)
    elif not args.log_fp.parent.exists():
        msg = f'--log_fp parent directory does not exist: {args.log_fp.parent}'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)
    if args.executor == 'aws' and not args.s3_bucket:
        msg = '--s3_bucket <bucket_uri> is required when using the aws executor'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)
    if args.s3_bucket and not args.executor == 'aws':
        msg = '--s3_bucket is only applicable when using the aws executor'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)
    if args.executor == 'aws' and not args.docker:
        log.render('info: aws executor requires docker but wasn\'t explicitly set, forcing')
        args.docker = True
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
    return [*paths_s3, *paths_local]
