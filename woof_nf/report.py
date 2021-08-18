import pathlib
import re
import subprocess
import sys
import textwrap
import time


import boto3


from . import aws
from . import log
from . import utility
from . import workflow


def render(
    comparison_dir: pathlib.Path,
    comparison_remote_dir,
    output_type,
    work_dir,
    executor
) -> None:
    log.task_msg_title('Rendering RMarkdown report')
    log.render_newline()
    if executor == 'aws':
        assert work_dir.startswith('s3://')
        render_aws(comparison_dir, comparison_remote_dir, output_type, work_dir)
    elif executor == 'local':
        render_local(comparison_dir, comparison_remote_dir, output_type)
    else:
        assert False


def submit_batch_job(command):
    # Construct job definition ARN and set job name
    job_definition_base = re.sub('[./:]', '-', workflow.DOCKER_URI_HUB)
    job_definition_arn = f'nf-{job_definition_base}'
    job_name = 'woof-report-creation'
    # Check job definition exists
    client = boto3.client('batch')
    response = client.describe_job_definitions(jobDefinitionName=job_definition_arn)
    if not response.get('jobDefinitions'):
        msg = f'could not find required job definition: {job_definition_arn}'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)
    log.render(f'    job definition: {job_definition_arn}')
    # Submit job
    response = client.submit_job(
        jobName=job_name,
        jobQueue=aws.BATCH_QUEUE,
        jobDefinition=job_definition_arn,
        containerOverrides={'memory': 4000, 'command': ['bash', '-o', 'pipefail', '-c', command]},
    )
    job_id = response.get('jobId')
    if not job_id:
        msg = f'unable to successfully submit job, got response:\n{response}'
        log.render(log.ftext(f'error: {msg}', c='red'))
        sys.exit(1)
    log.render(f'    job name (jobid): {job_name} ({job_id})')
    # Allow some time for Batch to recieve and process job
    time.sleep(10)
    # Poll job every 5 seconds and report status until it finishes
    status_other = {'SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING'}
    overwrite_status_line = False
    while True:
        # Get job info
        response = client.describe_jobs(jobs=[job_id])
        if not response.get('jobs'):
            msg = f'could not retrieve job information for job: {job_id}'
            log.render(log.ftext(f'\nerror: {msg}', c='red'))
            sys.exit(1)
        jobs_info = response.get('jobs')
        if len(jobs_info) != 1:
            msg = f'unexpected number of jobs for {job_id}, got response:\n{jobs_info}'
            log.render(log.ftext(f'\nerror: {msg}', c='red'))
            sys.exit(1)
        [job_info] = jobs_info
        # Check status
        job_status = job_info.get('status')
        if not job_status:
            msg = f'could not retrieve job status for {job_id}, got response:\n{job_info}'
            log.render(log.ftext(f'\nerror: {msg}', c='red'))
            sys.exit(1)
        elif job_status == 'FAILED':
            log.render('\u001b[F\u001b[0K', end='')
            log.render(f'    job status: {job_status}')
            msg = f'job {job_id} failed for the given reason: {job_info.get("statusReason")}'
            log.render(log.ftext(f'\nerror: {msg}', c='red'))
            sys.exit(1)
        elif job_status == 'SUCCEEDED':
            # Rewrite status line, then notify of completion
            log.render('\u001b[F\u001b[0K', end='')
            log.render(f'    job status: {job_status}')
            log.render('    job completed successfully!')
            break
        elif job_info.get('stoppedAt'):
            # NOTE: branch unlikely execute; status should already be set as FAILED and caught above
            reason_stop = job_info.get('statusReason')
            msg_base = f'job {job_id} was stopped early with status {job_status}'
            if reason_stop:
                log.render(log.ftext(f'\nerror: {msg_base} and given reason: {reason_stop}', c='red'))
            else:
                log.render(log.ftext(f'\nerror: {msg_base}. No reason was given.', c='red'))
            sys.exit(1)
        elif job_status in status_other:
            # Overwrite previous line (skip on first pass)
            if overwrite_status_line:
                log.render('\u001b[F\u001b[0K', end='')
            log.render(f'    job status: {job_status}')
            overwrite_status_line = True
            time.sleep(5)
        else:
            assert False


def render_aws(comparison_dir, comparison_remote_dir, output_type, work_dir):
    # Set excludes for comparison directory sync
    sync_excludes = '--exclude="*nextflow/*" --exclude="pipeline_log_*txt"'

    # Upload workflow files, and if needed up load output files
    lib_dir = utility.join_paths(str(pathlib.Path(__file__).parent), 'workflow/lib')
    lib_remote_dir = utility.join_paths(work_dir, 'other', 'workflow', 'lib')
    log.render(f'  uploading workflow lib directory to {lib_remote_dir}')
    utility.execute_command(f'aws s3 sync {lib_dir} {lib_remote_dir}')
    if output_type == 'local':
        comparison_remote_dir = utility.join_paths(work_dir, 'other', 'output')
        log.render(f'  uploading comparison results directory to {comparison_remote_dir}')
        utility.execute_command(f'aws s3 sync {sync_excludes} {comparison_dir} {comparison_remote_dir}')

    # Create command to run on Batch
    # Download workflow and comparison files
    commands = list()
    comparison_batch_dir = 'output/'
    lib_batch_dir = 'workflow/lib/'
    commands.append(f'aws s3 sync {lib_remote_dir} {lib_batch_dir}')
    commands.append(f'aws s3 sync {sync_excludes} {comparison_remote_dir} {comparison_batch_dir}')
    # Create R command
    report_entry_fp = utility.join_paths(lib_batch_dir, 'report.Rmd')
    output_fp = utility.join_paths(comparison_batch_dir, 'report.html')
    render_command = create_report_render_command(comparison_batch_dir, output_fp, report_entry_fp)
    commands.append(render_command)
    # Upload report
    if output_type == 's3':
        output_remote_fp = utility.join_paths(comparison_remote_dir, 'report.html')
    elif output_type == 'local':
        output_remote_fp = utility.join_paths(work_dir, 'other', 'output', 'report.html')
    commands.append(f'aws s3 cp {output_fp} {output_remote_fp}')

    # Submit Batch job and await
    # NOTE: commands are passed to Batch in the form: bash -c '<commands>', and so they must be
    # delimited by ';'. One complication to this is that BASH heredocs already define a delimited
    # and should have have a trailing ';'. We handle this in the loop below.
    commands_delimited = list()
    for command in commands:
        if not command.endswith('EOF'):
            command = f'{command}; '
        else:
            command = f'{command}\n'
        commands_delimited.append(command)
    command = ''.join(commands_delimited)
    log.render('  submitting report creation job to AWS Batch:')
    submit_batch_job(command)

    # Download result if needed
    if output_type == 'local':
        # NOTE: might be better practise to use boto3 here
        output_local_fp = utility.join_paths(str(comparison_dir), 'report.html')
        log.render(f'  downloading report {output_remote_fp} -> {output_local_fp}')
        utility.execute_command(f'aws s3 cp {output_remote_fp} {output_local_fp}')


def render_local(comparison_dir, comparison_remote_dir, output_type):
    # Execute
    output_fp = comparison_dir / 'report.html'
    report_entry_fp = pathlib.Path(__file__).parent / 'workflow/lib/report.Rmd'
    render_command = create_report_render_command(comparison_dir, output_fp, report_entry_fp)
    utility.execute_command(render_command)
    # Upload to s3 is required
    if output_type == 's3':
        output_remote_fp = utility.join_path(comparison_remote_dir, 'report.html')
        utility.execute_command(f'aws s3 cp {output_fp} {output_remote_fp}')


def create_report_render_command(comparison_dir, output_fp, report_entry_fp):
    rscript = textwrap.dedent(f'''
        library(fs)
        library(rmarkdown)

        # Absolute paths much be calculated prior to passing to rmarkdown::render
        s.output_file <- fs::path_abs('{output_fp}')
        s.results_directory <- fs::path_abs('{comparison_dir}')

        rmarkdown::render(
          '{report_entry_fp}',
          output_file=s.output_file,
          params=list(
            results_directory=s.results_directory
          )
        )
    ''')
    return f'R --vanilla <<EOF\n{rscript}\nEOF'
