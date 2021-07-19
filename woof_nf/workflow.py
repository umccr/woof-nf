import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional


from . import aws
from . import log


DOCKER_URI_AWS = f'{aws.ECR_BASE_URI}/{aws.ECR_REPO}:{aws.ECR_IMAGE_TAG}'
DOCKER_URI_HUB = f'docker.io/scwatts/woof-nf:0.1.1'

PROCESS_LINE_RE = re.compile(r'^\[[ -/0-9a-z]+\] process > (\S+).+?$')
STAGING_LINE_RE = re.compile(r'^Staging foreign file: (.+)$')
BIN_UPLOAD_LINE_RE = re.compile(r'^Uploading local `bin` scripts.+$')

AWS_COMPLETION = [
    'Completed at:',
    'Duration    :',
    'CPU hours   :',
    'Succeeded   :'
]


class RenderInfo:

    def __init__(self):
        self.title = str()
        self.executor = str()
        self.processes = dict()
        self.errors = list()
        # Line size and display count
        self.line_sizes = list()
        self.lines_displayed = 0
        # AWS file staging
        self.files_uploading = list()
        self.files_downloading = list()
        # We prevent re-rendering in case of multiple newlines with this flag
        self.newline_previous = False
        self.splash = True


def create_configuration(inputs_fp: pathlib.Path, output_dir: pathlib.Path, docker: bool, executor: str) -> pathlib.Path:
    # Get configuration
    config_lines = list()
    config_lines.append('// Inputs and outputs')
    config_lines.append(f'params.inputs_fp = "{inputs_fp}"')
    config_lines.append(f'params.output_dir = "{output_dir}"')
    config_lines.append('')
    config_lines.append('// Executor')
    if executor == 'aws':
        config_lines.append('process.executor = "awsbatch"')
        config_lines.append(f'process.queue = "{aws.BATCH_QUEUE}"')
        config_lines.append(f'aws.region = "{aws.REGION}"')
    elif executor == 'local':
        config_lines.append('process.executor = "local"')
    else:
        assert False
    if docker:
        if executor == 'aws':
            docker_uri = DOCKER_URI_AWS
        elif executor == 'local':
            docker_uri = DOCKER_URI_HUB
        else:
            assert False
        config_lines.append('docker.enabled = true')
        config_lines.append(f'process.container = "{docker_uri}"')
    # Write to disk
    output_fp = output_dir / 'nextflow.config'
    with output_fp.open('w') as fh:
        print(*config_lines, sep='\n', file=fh)
    return output_fp


def run(inputs_fp: pathlib.Path, output_dir: pathlib.Path, resume: bool, docker: bool, executor: str, bucket: str) -> None:
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
    log.render('\nNextflow output:\n')
    # Start
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        shell=True,
        universal_newlines=True,
    )
    # Stream output to terminal, replicating NF console logging
    errors = render_nextflow_lines(p)
    # Block until pipeline process exits
    p.wait()
    # Print errors and propagate erroneous return code
    if errors:
        error_str = ''.join(errors)
        log.render(error_str)
    if p.returncode != 0:
        sys.exit(1)


def render_nextflow_lines(p: subprocess.Popen) -> List[str]:
    # NOTE: type checking requires p.stdout not to be None
    if not p.stdout:
        assert False
    # Process lines
    ri = RenderInfo()
    for line in p.stdout:
        # Allow re-rendering if current line and last are not newlines
        if line != '\n' and ri.newline_previous:
            ri.newline_previous = False
        # Begin main line handling
        if line.startswith('N E X T F L O W'):
            ri.title = f'    {line}'
        elif line.startswith('Launching') or line.startswith('executor >'):
            ri.executor = f'    {line}'
        elif process_match := PROCESS_LINE_RE.match(line):
            process_name = process_match.group(1)
            ri.processes[process_name] = f'    {line}'
        elif aws_staging_match := STAGING_LINE_RE.match(line):
            # S3:// files always downloaded; local files always uploaded
            staging_file = aws_staging_match.group(1)
            if staging_file.startswith('s3://'):
                ri.files_downloading.append(staging_file)
            else:
                ri.files_uploading.append(staging_file)
        elif bin_upload_match := BIN_UPLOAD_LINE_RE.match(line):
            # Not considered important
            pass
        elif any(line.startswith(p) for p in AWS_COMPLETION):
            # Not considered important - completion status, only present with AWS
            pass
        elif line == '\n':
            # Ignore here, used to decide when to render below
            pass
        elif line.rstrip() == '':
            # AWS nf plugin produces lines containing only spaces, ignore
            pass
        else:
            ri.errors.append(f'    {line}')
        # Render when:
        #   - end of 'process' block (general case)
        #   - first pass to allow quick header/splash display
        if (line == '\n' and not ri.newline_previous) or ri.splash:
            term_size = shutil.get_terminal_size()
            ri.lines_displayed = sum(get_actual_lines(ri.line_sizes, term_size))
            ri.line_sizes = render_output(ri, term_size)
            # Clear files staging info and set previous newline variable
            ri.files_uploading = list()
            ri.files_downloading = list()
            ri.newline_previous = True
            # Disable splash if we have both title and executor
            ri.splash = not (ri.title and ri.executor)
    # Clear output so we can print full and final text
    term_size = shutil.get_terminal_size()
    clear_terminal(term_size, ri.lines_displayed)
    # Get final output
    status = [
        ri.title,
        ri.executor,
        *ri.processes.values()
    ]
    status_str = ''.join(status)
    log.render(status_str, sep='')
    return ri.errors


def get_actual_lines(line_sizes: List[int], term_size: os.terminal_size) -> List[int]:
    lines_actual = list()
    for line_size in line_sizes:
        lines = math.ceil(line_size / term_size.columns)
        lines_actual.append(max(1, lines))
    return lines_actual


def clear_terminal(term_size: os.terminal_size, lines_displayed: int) -> None:
    # Set cursor to first rewrite line then clear to end of terminal
    lines_rewrite = min(term_size.lines, lines_displayed)
    if lines_displayed:
        sys.stdout.write(f'\u001b[{lines_rewrite}A')
        sys.stdout.write('\u001b[0J')


def render_output(ri, term_size: os.terminal_size) -> List[int]:
    # Clear terminal
    clear_terminal(term_size, ri.lines_displayed)
    # Prepare new lines
    lines_all: List[str] = list()
    lines_all.append(ri.title)
    lines_all.append(ri.executor)
    lines_all.extend(ri.processes.values())
    # Staging blocked; nested if statements to pad block with newlines
    if ri.files_uploading or ri.files_downloading:
        lines_all.append('\n')
        if ri.files_uploading:
            files_n = len(ri.files_uploading)
            plurality = 'file' if files_n == 1 else 'files'
            lines_all.append(f'Currently uploading {len(ri.files_uploading)} {plurality} to S3\n')
        if ri.files_downloading:
            files_n = len(ri.files_uploading)
            plurality = 'file' if files_n == 1 else 'files'
            lines_all.append(f'Currently downloading {len(ri.files_downloading)} {plurality} from S3\n')
        lines_all.append('\n')
    lines_all.append('\n')
    if ri.errors:
        lines_all.append(
            'Errors encountered - check .nextflow.log for further information!'
            ' Further details will be printed at conclusion of workflow run.\n'
        )
        lines_all.append('\n')
    # Remove empty lines
    lines: List[str] = [line for line in lines_all if line]
    # Set max display lines, get actual number of lines that will be displayed while accounting for line wrapping
    lines_print_max = term_size.lines - 1
    line_sizes = [len(l) - 1 for l in lines]
    lines_actual = get_actual_lines(line_sizes, term_size)
    # Select lines to display such that we don't exceed number of available lines
    line_index: Optional[int] = None
    lines_actual_sum = 0
    for i, la in enumerate(lines_actual[::-1], 1):
        lines_actual_sum += la
        if lines_actual_sum > lines_print_max:
            break
        line_index = i
    # If the terminal is too small to display normal messages, indicate. Otherwise display nf
    # output
    if line_index:
        lines = lines[-line_index:]
        line_sizes = line_sizes[-line_index:]
        for line in lines:
            sys.stdout.write(line)
    else:
        message = 'Terminal size too small to print message\n'
        sys.stdout.write(message)
        line_sizes = [len(message) - 1]
    return line_sizes


def print_line(line, line_sizes) -> None:
    sys.stdout.write(line)
    line_size = max(1, len(line) - 1)
    line_sizes.append(line_size)
