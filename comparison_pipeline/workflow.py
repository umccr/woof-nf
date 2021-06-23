import math
import pathlib
import re
import shutil
import subprocess
import sys


from . import log


docker_uri = '843407916570.dkr.ecr.ap-southeast-2.amazonaws.com/comparison_pipeline:0.0.1'

process_line_re = re.compile(r'^\[[ -/0-9a-z]+\] process > (.+?) [()0-9 -]+.*$')
staging_line_re = re.compile(r'^Staging foreign file: (.+)$')
bin_upload_line_re = re.compile(r'^Uploading local `bin` scripts.+$')


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
        config_lines.append('process.queue = "nextflow-job-queue"')
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
    errors = render_nextflow_lines(p)
    # Block until pipeline process exits
    p.wait()
    # Check returncode
    if p.returncode != 0:
        error_str = ''.join(errors)
        log.render(error_str)
        sys.exit(1)


def render_nextflow_lines(p):
    title = str()
    executor = str()
    processes = dict()
    errors = list()

    line_sizes = list()

    for line in p.stdout:
        if line.startswith('N E X T F L O W'):
            title = f'    {line}'
        elif line.startswith('Launching') or line.startswith('executor >'):
            executor = f'    {line}'
        elif process_match := process_line_re.match(line):
            process_name = process_match.group(1)
            processes[process_name] = f'    {line}'
        elif aws_staging_match := staging_line_re.match(line):
            staging_file = aws_staging_match.group(1)

        elif bin_upload_match := bin_upload_line_re.match(line):
            pass

        elif line == '\n':
            term_size = shutil.get_terminal_size()
            lines_displayed = sum(get_actual_lines(line_sizes, term_size))
            line_sizes = render_output(
                title,
                executor,
                processes,
                errors,
                lines_displayed,
                term_size
            )
        else:
            errors.append(f'    {line}')
    # Clear output so we can print full and final text
    term_size = shutil.get_terminal_size()
    clear_terminal(term_size, lines_displayed)
    # Get final output
    status = [
        title,
        executor,
        *processes.values()
    ]
    status_str = ''.join(status)
    log.render(status_str, sep='')
    return errors


def get_actual_lines(line_sizes, term_size):
    lines_actual = list()
    for line_size in line_sizes:
        lines = math.ceil(line_size / term_size.columns)
        lines_actual.append(max(1, lines))
    return lines_actual


def clear_terminal(term_size, lines_displayed):
    # Set cursor to first rewrite line then clear to end of terminal
    lines_rewrite = min(term_size.lines, lines_displayed)
    if lines_displayed:
        sys.stdout.write(f'\u001b[{lines_rewrite}A')
        sys.stdout.write('\u001b[0J')


def render_output(title, executor, processes, errors, lines_displayed, term_size):
    # Clear terminal
    clear_terminal(term_size, lines_displayed)
    # Prepare new lines
    lines = list()
    lines.append(title)
    lines.append(executor)
    lines.extend(processes.values())
    lines.append('\n')
    if errors:
        lines.append(
            'Errors encountered - check <file> for further information!'
            ' Details will be printed at conclusion of workflow run.\n'
        )
        lines.append('\n')
    # Select lines to display; at most all available terminal lines except one
    lines_print = min(term_size.lines - 1, len(lines))
    # Get actual number of lines that will be displayed, account for line wrapping
    line_sizes = [len(l) - 1 for l in lines]
    lines_actual = get_actual_lines(line_sizes, term_size)
    # Select lines to display such that we don't exceed number of available lines
    line_index = None
    lines_actual_sum = 0
    for i, la in enumerate(lines_actual[::-1], 1):
        lines_actual_sum += la
        if lines_actual_sum > lines_print:
            break
        line_index = i
    # If the terminal is too small to display normal messages, indicate. Otherwise display nf
    # output
    if line_index == None:
        message = 'Terminal size too small to print message\n'
        sys.stdout.write(message)
        line_sizes = [len(message) - 1]
    else:
        lines = lines[-line_index:]
        line_sizes = line_sizes[-line_index:]
        for line in lines:
            sys.stdout.write(line)
    return line_sizes


def print_line(line, line_sizes):
    sys.stdout.write(line)
    line_size = max(1, len(line) - 1)
    line_sizes.append(line_size)
