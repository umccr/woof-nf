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
from . import utility


DOCKER_URI_AWS = f'{aws.ECR_BASE_URI}/{aws.ECR_REPO}:{aws.ECR_IMAGE_TAG}'
DOCKER_URI_HUB = f'docker.io/scwatts/woof-nf:0.2.3'

PROCESS_LINE_RE = re.compile(r'^\[[ -/0-9a-z]+\] process > (\S+).+?$')
STAGING_LINE_RE = re.compile(r'^Staging foreign file: (.+)$')
RETRY_LINE_RE = re.compile(r'^\[[ -/0-9a-z]+\] NOTE: Process.+?Execution is retried.+?$')
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
        self.info = set()
        # Line size and display count
        self.line_sizes = list()
        self.lines_displayed = 0
        # AWS file staging
        self.files_uploading = list()
        self.files_downloading = list()
        # We prevent re-rendering in case of multiple newlines with this flag
        self.newline_previous = False
        self.splash = True
        # Extra status flags
        self.killing_tasks = False
        self.transfering_files = False


def create_configuration(
    inputs_fp: pathlib.Path,
    output_dir: pathlib.Path,
    nextflow_run_dir: pathlib.Path,
    docker: bool,
    executor: str
) -> pathlib.Path:
    # Copy in defaults
    default_config_src_fp = pathlib.Path(__file__).parent / 'workflow/defaults.config'
    default_config_fp = nextflow_run_dir / 'defaults.config'
    shutil.copy(default_config_src_fp, default_config_fp)
    # Get configuration
    config_lines = list()
    config_lines.append('// Inputs and outputs')
    config_lines.append(f'params.inputs_fp = "{inputs_fp}"')
    config_lines.append(f'params.output_dir = "{output_dir}"')
    config_lines.append(f'params.nextflow_run_dir = "{nextflow_run_dir}"')
    config_lines.append(f'params.publish_mode = "copy"')
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
    # Include defaults.config
    config_lines.append(f'includeConfig "{default_config_fp.absolute()}"')
    # Write to disk
    output_fp = nextflow_run_dir / 'nextflow.config'
    with output_fp.open('w') as fh:
        print(*config_lines, sep='\n', file=fh)
    return output_fp


def run(
    inputs_fp: pathlib.Path,
    output_type: str,
    output_dir: pathlib.Path,
    output_remote_dir: pathlib.Path,
    nextflow_dir: pathlib.Path,
    work_dir: pathlib.Path,
    run_timestamp: str,
    resume: bool,
    docker: bool,
    executor: str
) -> None:
    # Set the actual final output directory.
    # We allow operation in 'local' and 'remote' mode. For remote mode, files are written to an S3
    # bucket from AWS Batch instances but execution of Nextflow still requires local configuration
    # files and logs can also only be written locally. For a (hopefully) simple solution, I have
    # decided to allow output_dir to have different meanings in remote and local operation modes:
    #
    #   * local mode: output_dir refers to the final output directory for file
    #   * remote mode: output_dir refers to the local directory containing config and logs
    #
    # This now only requires us to set the final output directory in remote mode to the requested
    # S3 path, which is stored in output_remote_dir.
    if output_type == 'local':
        output_dir_final = output_dir
    elif output_type == 's3':
        output_dir_final = output_remote_dir
    else:
        assert False
    # Create directory for nextflow logs and reports
    nextflow_run_dir = nextflow_dir / run_timestamp
    nextflow_run_dir.mkdir(mode=0o700)
    # Create workflow config, set log filepath, and set work directory
    config_fp = create_configuration(inputs_fp, output_dir_final, nextflow_run_dir, docker, executor)
    log_fp = nextflow_run_dir / 'nextflow_log.txt'
    if output_type == 's3':
        utility.upload_nextflow_dir(nextflow_dir, output_remote_dir)
    # Prepare command and args
    command_tokens = list()
    command_tokens.append('nextflow')
    command_tokens.append(f'-log {log_fp}')
    command_tokens.append('run')
    command_tokens.append(f'-config {config_fp}')
    command_tokens.append(f'-work-dir {work_dir}')
    if resume:
        command_tokens.append('-resume')
    workflow_fp = pathlib.Path(__file__).parent / 'workflow/pipeline.nf'
    command_tokens.append(workflow_fp)
    # Construct full command
    log.task_msg_title('Executing workflow')
    command = ' '.join(str(p) for p in command_tokens)
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
    if output_type == 's3':
        utility.upload_nextflow_dir(nextflow_dir, output_remote_dir)
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
        elif line.startswith('WARN: Killing pending tasks'):
            ri.killing_tasks = True
        elif line.startswith('WARN'):
            ri.info.add(line)
        elif RETRY_LINE_RE.match(line):
            ri.transfering_files = True
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
        # Reset extra status flags
        ri.killing_tasks = False
        ri.transfering_files = False
    # Clear output so we can print full and final text
    term_size = shutil.get_terminal_size()
    clear_terminal(term_size, ri.lines_displayed)
    # Get final output
    status = [
        ri.title,
        ri.executor,
        *ri.processes.values(),
        '\n',
        *ri.info,
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
    # Staging block; nested if statements to pad block with newlines
    lines_all.append('\n')
    if ri.files_uploading or ri.files_downloading:
        if ri.files_uploading:
            files_n = len(ri.files_uploading)
            plurality = 'file' if files_n == 1 else 'files'
            lines_all.append(f'Currently uploading {len(ri.files_uploading)} {plurality} to S3\n')
        if ri.files_downloading:
            files_n = len(ri.files_uploading)
            plurality = 'file' if files_n == 1 else 'files'
            lines_all.append(f'Currently downloading {len(ri.files_downloading)} {plurality} from S3\n')
        lines_all.append('\n')
    if ri.killing_tasks:
        lines_all.append('Nextflow is killing tasks, please wait\n')
        lines_all.append('\n')
    if ri.transfering_files:
        lines_all.append('Nextflow is transfering files, please wait\n')
        lines_all.append('\n')
    if ri.errors or ri.info:
        lines_all.append(
            'Undisplayed messages - details will be printed at the conclusion of the workflow '
            'run. Please check the nextflow log for further details.\n'
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
