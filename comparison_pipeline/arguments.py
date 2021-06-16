import argparse
import multiprocessing
import pathlib


from . import log


def collect():
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
        '--threads',
        type=int,
        default=multiprocessing.cpu_count(),
        help='Number of threads to utilise'
    )

    parser.add_argument(
        '--executor',
        choices=('local', 'aws'),
        default='local',
        help='Workflow executor'
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


def check(args):
    log.task_msg_title('Checking arguments')
    log.task_msg_body('Not yet implemented - hold on to your seats!\n')
    log.render('Free pass for now :)\n')
