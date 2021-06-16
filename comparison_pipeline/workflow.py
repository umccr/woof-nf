import pathlib
import subprocess
import sys


from . import log


docker_uri = '843407916570.dkr.ecr.ap-southeast-2.amazonaws.com/comparison_pipeline:0.0.1'


def run(inputs_fp, output_dir, resume, docker, executor, bucket):
    # Set workflow configuration
    args = list()
    args.append(f'--inputs_fp {inputs_fp}')
    args.append(f'--output_dir {output_dir}')
    if resume:
        args.append('-resume')
    if docker:
        args.append(f'-with-docker {docker_uri}')
    if executor == 'aws':
        args.append('-process.executor awsbatch')
        args.append('-process.queue nextflow-testing-job-queue')
        args.append(f'-bucket-dir {bucket}')
    elif executor == 'local':
        args.append('-process.executor local')
    else:
        assert False
    args_str = ' '.join(args)
    # Prepare full command
    log.task_msg_title('Executing workflow')
    workflow_fp = pathlib.Path(__file__).parent / 'workflow/pipeline.nf'
    command = f'{workflow_fp} {args_str}'
    log.render(log.ftext(f'\nCommand: {command}', f='bold'))
    # Start
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        shell=True,
        universal_newlines=True,
    )
    # Stream output to terminal, replicating behaviour
    log.render('\nNextflow output:')
    # Print initial block (block delimiter as an empty newline)
    displayed_lines = 0
    for line in p.stdout:
        if line == '\n':
            break
        sys.stdout.write(f'    {line}')
        displayed_lines += 1
    sys.stdout.write('\n')
    displayed_lines += 1
    lines_rewrite = displayed_lines - 2
    # For each new block, rewrite all but first two lines
    lines = list()
    for line in p.stdout:
        if line == '\n':
            # End of block
            # Set cursor to first rewrite line
            sys.stdout.write(f'\u001b[{lines_rewrite}A')
            # Clear to end of terminal
            sys.stdout.write('\u001b[0J')
            # Write new lines, prepare for next block
            print(''.join(lines))
            lines_rewrite = len(lines) + 1
            lines = list()
        else:
            # In block
            lines.append(f'    {line}')
    # Block until pipeline process exits
    p.wait()
    # Check returncode
    if p.returncode != 0:
        stderr_str = ''.join(l for l in p.stderr)
        log.render(f'error:\n{stderr_str}')
        sys.exit(1)
