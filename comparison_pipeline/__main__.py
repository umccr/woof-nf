#!/usr/bin/env python3
import sys


from . import __version__
from . import arguments
from . import dependencies
from . import inputs
from . import log
from . import report
from . import umccrise
from . import workflow


def entry():
    # TODO: splash

    # Print entry
    # TODO: further description of what will be done
    msg_body_text = (
        'Welcome to the UMCCR comparison pipeline\n'
    )
    log.task_msg_title('Starting comparison pipeline')
    log.task_msg_body(msg_body_text)

    # Get and check command line arguments
    args = arguments.collect()
    args = arguments.check_and_process(args)

    log.render(log.ftext(f'Command: {" ".join(sys.argv)}\n', f='bold'))
    log.render('Info:')
    log.render(f'  version: {__version__}')
    log.render(f'  executor: {args.executor}')
    log.render(f'  docker: {"yes" if args.docker else "no"}')
    log.render(f'  s3_bucket: {args.s3_bucket if args.s3_bucket else "n/a"}')
    log.render(f'  resume: {"yes" if args.resume else "no"}\n')

    # Check dependencies
    dependencies.check(args.executor)

    # Get inputs and write to file
    input_list = umccrise.get_inputs(args.run_dir_one, args.run_dir_two)
    inputs_fp = inputs.write(input_list, args.output_dir / 'input_files.tsv')

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
