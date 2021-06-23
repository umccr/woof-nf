#!/usr/bin/env python3
import sys


from . import arguments
from . import aws
from . import dependencies
from . import information
from . import inputs
from . import log
from . import report
from . import umccrise
from . import workflow


def entry():
    # TODO: splash

    # Print entry
    # TODO: further description of what will be done
    log.task_msg_title('Starting comparison pipeline')
    log.task_msg_body('Welcome to the UMCCR comparison pipeline\n')

    # Get and check command line arguments
    args = arguments.collect()
    args = arguments.check_and_process(args)

    # Log some info to console
    log.task_msg_title('Logging pipeline configuration')
    log.render_newline()
    log.render(log.ftext(f'Command: {" ".join(sys.argv)}\n', f='bold'))
    log.render('Info:')
    information.render_info_table(args)
    log.render_newline()

    # Check dependencies, and test AWS auth and config if needed
    dependencies.check(args.executor, args.docker)
    if args.executor == 'aws': aws.check_config()

    # Get inputs and write to file
    input_data = inputs.collect(args.run_dir_one, args.run_dir_two)
    inputs_fp = inputs.write(input_data, args.output_dir / 'input_files.tsv')

    # Execute pipeline
    workflow.run(
        inputs_fp,
        args.output_dir,
        args.resume,
        args.docker,
        args.executor,
        args.s3_bucket
    )

    # Render report
    report.render(args.output_dir)

    # Exit message
    log.task_msg_title('Pipeline completed sucessfully! Goodbye')


if __name__ == '__main__':
    entry()
