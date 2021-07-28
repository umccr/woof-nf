import argparse
import datetime
import os
import pathlib
import sys
import tempfile
import textwrap


from . import log
from . import utility


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
            if args.output_remote_dir:
                msg = '--work_dir required with local output and AWS executor'
                log.render(log.ftext(f'error: {msg}', c='red'))
                sys.exit(1)
            else:
                args.work_dir = utility.join_paths(args.output_remote_dir, 'nextflow/work')
        elif not args.work_dir.startswith('s3://'):
            msg = textwrap.dedent('''
                AWS job execution requires S3 work directory, remove --work-dir or manually set
                to S3 path
            ''').strip().replace('\n', '')
            log.render(log.ftext(f'error: {msg}', c='red'))
            sys.exit(1)
    elif args.executor == 'local' and not args.work_dir:
        args.work_dir = str(args.nextflow_dir / 'work')

    if args.work_dir.startswith('s3://') and not args.output_type == 's3' and not args.force:
        msg = 'refusing to use a S3 work directory with local output without --force'
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
        log.render('\ninfo: aws executor requires docker but wasn\'t explicitly set, forcing\n')
        args.docker = True

    # Create local output directories
    if args.output_type == 'local' and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)
    if args.output_type == 'local' and not os.path.exists(args.nextflow_dir):
        os.makedirs(args.nextflow_dir, exist_ok=True)

    # Set up log file
    args.run_timestamp = '{:%Y%m%d_%H%M%S}'.format(datetime.datetime.now())
    log_fn = f'pipeline_log_{args.run_timestamp}.txt'
    if not args.log_fp:
        args.log_fp = pathlib.Path(args.output_dir, log_fn)
    elif args.log_fp.startswith('s3://'):
        msg = 'custom log directories on S3 are not allowed'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)

    if not args.log_fp.parent.exists():
        msg = f'--log_fp parent directory does not exist: {args.log_fp.parent}'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)
    log.setup_log_file(args.log_fp)
    return args
