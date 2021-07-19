import argparse
import multiprocessing
import pathlib
import sys


from . import log


def collect() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--run_dir_one',
        required=True,
        nargs='+',
        type=pathlib.Path,
        help='Space separated list of run directories'
    )
    parser.add_argument(
        '--run_dir_two',
        required=True,
        nargs='+',
        type=pathlib.Path,
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
        help='S3 bucket directory to use with AWS executor'
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

    if args.log_fp == None:
        args.log_fp = args.output_dir / 'pipeline_log.txt'
        log.setup_log_file(args.log_fp)

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
