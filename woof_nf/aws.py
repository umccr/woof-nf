import subprocess
import sys


from . import log
from . import table


REGION = 'ap-southeast-2'
ACCOUNT = '843407916570'
BATCH_QUEUE = 'nextflow-job-queue'


def check_config() -> None:
    log.task_msg_title('Checking AWS credentials and config')
    log.render_newline()
    # Define output table
    header_row = table.Row(('Item', 'Result'), header=True)
    rows_check = {
        'auth': table.Row(('Authentication', table.Cell('not checked', c='black'))),
        'job_queue': table.Row(('Job queue', table.Cell('not checked', c='black'))),
    }
    # Authentication
    errors = list()
    errors_auth = check_authentication()
    if errors_auth:
        set_row_failed(rows_check['auth'])
        render_table_and_errors(header_row, rows_check, errors_auth)
        sys.exit(1)
    else:
        set_row_passed(rows_check['auth'])
    # Job queue
    errors_job_queue = check_job_queue()
    if errors_job_queue:
        errors.extend(errors_job_queue)
        set_row_failed(rows_check['job_queue'], text='not found')
    else:
        set_row_passed(rows_check['job_queue'], text='found')
    # Render results and quit if any errors encountered
    render_table_and_errors(header_row, rows_check, errors)
    if errors:
        sys.exit(1)


def check_authentication():
    command = 'aws sts get-caller-identity'
    fail_message = 'could not verify AWS authentication with STS'
    result, errors = aws_command(command, fail_message)
    return errors


def check_job_queue():
    command = r'''
        aws batch describe-job-queues \
            --output text \
            --no-paginate \
            --query 'jobQueues[].jobQueueName'
    '''
    fail_message = 'could not retrieve Batch job queues'
    result, errors = aws_command(command, fail_message)
    if errors:
        return errors
    errors = list()
    job_queues = set(result.stdout.rstrip().split())
    if BATCH_QUEUE not in job_queues:
        errors.append(log.ftext(
            f'\nerror: could not find requested job queue \'{BATCH_QUEUE}\', found:',
            c='red')
        )
        for job_queue in job_queues:
            errors.append(f'\t{job_queue}')
        return errors


def aws_command(command: str, fail_message: str) -> subprocess.CompletedProcess:
    # Remove excessive whitespace/newlines so that we can append --region
    command_full = f'{command.rstrip()} --region {REGION}'
    result = subprocess.run(
        command_full,
        shell=True,
        capture_output=True,
        encoding='utf-8'
    )
    errors = list()
    if result.returncode != 0:
        errors.append(log.ftext(f'\nerror: {fail_message}:', c='red'))
        errors.append(f'command: {command_full}')
        errors.append(f'stdout: {result.stdout}')
        errors.append(f'stderr: {result.stderr}')
    return result, errors


def set_row_failed(row, text='fail'):
    update_result_cell(row.cells[1], text, 'red')


def set_row_passed(row, text='pass'):
    update_result_cell(row.cells[1], text, 'green')


def update_result_cell(cell, text, colour):
    cell.text = text
    cell.c = colour


def render_table_and_errors(header_row, rows, errors):
    table.render_table([header_row, *rows.values()])
    log.render_newline()
    log.render('\n'.join(errors))
