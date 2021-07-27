#!/usr/bin/env python3
import sys


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
    if args.executor == 'aws': aws.check_config()

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

    # Exit message
    log.task_msg_title('Pipeline completed sucessfully! Goodbye')
    if args.output_type == 's3':
        utility.upload_log(args.log_fp, args.output_remote_dir)


if __name__ == '__main__':
    entry()
