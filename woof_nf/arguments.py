import argparse
import multiprocessing
import pathlib
import re
import sys


import s3path


from . import log


S3_PATH_RE = re.compile(r'^s3:/(/.+)$')


# NOTE: this probably fits better elsewhere but we assign down below
class S3PathOverride(s3path.S3Path):

    def __str__(self):
        # Override to print S3 path with full URI
        return f's3:/{super().__str__()}'


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
    log.task_msg_title('Checking arguments')
    log.render_newline()
    # Cast inputs to pathlib.Path or s3path.S3Path
    args.run_dir_one = process_input_directories(args.run_dir_one)
    args.run_dir_two = process_input_directories(args.run_dir_two)
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


def process_input_directories(run_dir):
    run_dir_cast = list()
    for dirpath in run_dir:
        if dirpath.startswith('s3'):
            re_result = S3_PATH_RE.match(dirpath)
            if not re_result:
                assert False
            run_dir_cast.append(S3PathOverride(re_result.group(1)))
        else:
            run_dir_cast.append(pathlib.Path(dirpath))
    return run_dir_cast
