import pathlib
import subprocess
import sys


from . import log


docker_uri = '843407916570.dkr.ecr.ap-southeast-2.amazonaws.com/comparison_pipeline:0.0.1'


def create_configuration(inputs_fp, output_dir, docker, executor):
    # Get configuration
    config_lines = list()
    config_lines.append('// Inputs and outputs')
    config_lines.append(f'params.inputs_fp = "{inputs_fp}"')
    config_lines.append(f'params.output_dir = "{output_dir}"')
    config_lines.append('')
    config_lines.append('// Executor')
    if executor == 'aws':
        config_lines.append('process.executor = "awsbatch"')
        config_lines.append('process.queue = "nextflow-testing-job-queue"')
        config_lines.append('aws.region = "ap-southeast-2"')
    elif executor == 'local':
        config_lines.append('process.executor = "local"')
    else:
        assert False
    if docker:
        config_lines.append('docker.enabled = true')
        config_lines.append(f'process.container = "{docker_uri}"')
    # Write to disk
    output_fp = output_dir / 'nextflow.config'
    with output_fp.open('w') as fh:
        print(*config_lines, sep='\n', file=fh)
    return output_fp


def run(inputs_fp, output_dir, resume, docker, executor, bucket):
    # Set workflow configuration
    config_fp = create_configuration(inputs_fp, output_dir, docker, executor)
    # Set command line arguments
    args = list()
    args.append(f'-c {config_fp}')
    if resume:
        args.append('-resume')
    if executor == 'aws':
        args.append(f'-bucket-dir {bucket}')
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
