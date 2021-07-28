import subprocess
import sys


from . import log
from . import table


REGION = 'ap-southeast-2'
BATCH_QUEUE = 'nextflow-job-queue'
ECR_BASE_URI = '843407916570.dkr.ecr.ap-southeast-2.amazonaws.com'
ECR_REPO = 'woof-nf'
ECR_IMAGE_TAG = '0.2.1'


def check_config() -> None:
    log.task_msg_title('Checking AWS credentials and config')
    log.render_newline()
    # Define output table
    header_row = table.Row(('Item', 'Result'), header=True)
    rows_check = {
        'auth': table.Row(('Authentication', table.Cell('not checked', c='black'))),
        'job_queue': table.Row(('Job queue', table.Cell('not checked', c='black'))),
        'ecr_repo': table.Row(('ECR repo', table.Cell('not checked', c='black'))),
        'ecr_image_tag': table.Row(('ECR image tag', table.Cell('not checked', c='black')))
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
    # ECR repo
    errors_ecr_repo = check_ecr_repo()
    if errors_ecr_repo:
        errors.extend(errors_ecr_repo)
        set_row_failed(rows_check['ecr_repo'], text='not found')
    else:
        set_row_passed(rows_check['ecr_repo'], text='found')
    # ECR image tag
    if not errors_ecr_repo:
        errors_ecr_image_tag = check_ecr_image_tag()
        if errors_ecr_image_tag:
            errors.extend(errors_ecr_image_tag)
            set_row_failed(rows_check['ecr_image_tag'], text='not found')
        else:
            set_row_passed(rows_check['ecr_image_tag'], text='found')
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


def check_ecr_repo():
    command = r'''
        aws ecr describe-repositories \
            --output text \
            --no-paginate \
            --query 'repositories[].repositoryName'
    '''
    fail_message = 'could not retrieve ECR repositories'
    result, errors = aws_command(command, fail_message)
    if errors:
        return errors
    ecr_repos = set(result.stdout.rstrip().split())
    errors = list()
    if ECR_REPO not in ecr_repos:
        errors.append(log.ftext(
            f'\nerror: could not find requested ECR repository \'{ECR_REPO}\', found:',
            c='red')
        )
        for repo in ecr_repos:
            errors.append(f'\t{repo}')
        return errors


def check_ecr_image_tag():
    command = fr'''
        aws ecr describe-images \
            --repository-name {ECR_REPO} \
            --output text \
            --no-paginate \
            --query 'imageDetails[].imageTags'
    '''
    fail_message = 'could not retrieve ECR image info'
    result, errors = aws_command(command, fail_message)
    if errors:
        return errors
    errors = list()
    tag_lists = [result.stdout.rstrip().split()]
    tags = {tag for tag_list in tag_lists for tag in tag_list}
    errors = list()
    if ECR_IMAGE_TAG not in tags:
        errors.append(log.ftext(
            f'\nerror: could not find requested image tag \'{ECR_IMAGE_TAG}\', found:',
            c='red')
        )
        for tag in tags:
            errors.append(f'\t{tag}')
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
