#!/usr/bin/env python3
import sys


from . import __prog__
from . import __version__
from . import arguments
from . import aws
from . import dependencies
from . import information
from . import inputs
from . import log
from . import report
from . import utility
from . import workflow


def entry():
    # Output program name and version neatly if requested
    if set(sys.argv) & {'-v', '--version'}:
        print(f'{__prog__} {__version__}')
        sys.exit()

    # Print entry
    log.task_msg_title('Starting the woof-nf pipeline')
    log.task_msg_body('Welcome to the UMCCR variant comparison pipeline\n')

    # Get and check command line arguments
    args = arguments.collect()
    args = arguments.check_and_process(args)

    # Log some info to console
    log.task_msg_title('Logging pipeline configuration')
    log.render_newline()
    log.render(log.ftext(f'Command: {" ".join(sys.argv)}\n', f='bold'))
    log.render('Info:')
    information.render_table(args)
    log.render_newline()

    # Check dependencies, and test AWS auth and config if needed
    dependencies.check(args.executor, args.docker)
    paths_all = [*args.run_dir_one, *args.run_dir_two, str(args.output_dir)]
    if args.executor == 'aws' or any(p.startswith('s3://') for p in paths_all):
        aws.check_config()

    # Process input paths; create pathlib.Path or s3path.VirtualPath
    # Performing here after AWS checks, so that S3 requests do not fail
    log.task_msg_title('Processing input directories')
    log.render_newline()
    args.run_dir_one = utility.process_input_directories(args.run_dir_one, run='one')
    args.run_dir_two = utility.process_input_directories(args.run_dir_two, run='two')
    log.render_newline()

    # Get inputs and write to file
    input_data = inputs.collect(args.run_dir_one, args.run_dir_two)
    inputs_fp = inputs.write(input_data, args.output_dir / 'nextflow/input_files.tsv')
    if args.output_type == 's3':
        utility.upload_log_and_config(args.log_fp, args.nextflow_dir, args.output_remote_dir)

    # Execute pipeline and render report
    workflow.run(
        inputs_fp,
        args.output_type,
        args.output_dir,
        args.output_remote_dir,
        args.nextflow_dir,
        args.work_dir,
        args.run_timestamp,
        args.resume,
        args.docker,
        args.executor
    )
    if args.output_type == 's3':
        utility.upload_log_and_config(args.log_fp, args.nextflow_dir, args.output_remote_dir)
    report.render(args.output_dir)

    # Diplay exit message, and upload logs if required
    log.task_msg_title('Pipeline completed sucessfully! Goodbye')
    if args.output_type == 's3':
        utility.upload_log(args.log_fp, args.output_remote_dir)


if __name__ == '__main__':
    entry()
