import subprocess
import sys


from . import log


region = 'ap-southeast-2'
batch_queue = 'nextflow-job-queue'
ecr_repo = 'comparison_pipeline'
ecr_image_tag = '0.0.1'


def check_config():
    log.task_msg_title('Checking AWS credentials and config')
    log.render_newline()
    # Authentication
    command = 'aws sts get-caller-identity'
    fail_message = 'could not verify AWS authentication with STS'
    aws_command(command, fail_message)
    # Job queue
    command = r'''
        aws batch describe-job-queues \
            --output text \
            --no-paginate \
            --query 'jobQueues[].jobQueueName'
    '''
    fail_message = 'could not retrieve Batch job queues'
    result = aws_command(command, fail_message)
    job_queues = set(result.stdout.rstrip().split())
    if batch_queue not in job_queues:
        log.render(log.ftext('\nerror: could not find requested job queue, found:', c='red'))
        for job_queue in job_queues:
            log.render(f'\t{job_queue}')
        sys.exit(1)
    # ECR repo
    command = r'''
        aws ecr describe-repositories \
            --output text \
            --no-paginate \
            --query 'repositories[].repositoryName'
    '''
    fail_message = 'could not retrieve ECR repositories'
    result = aws_command(command, fail_message)
    ecr_repos = set(result.stdout.rstrip().split())
    if ecr_repo not in ecr_repos:
        log.render(log.ftext('\nerror: could not find requested ECR repository, found:', c='red'))
        for repo in ecr_repos:
            log.render(f'\t{repo}')
        sys.exit(1)
    # ECR image tag
    command = r'''
        aws ecr describe-images \
            --repository-name comparison_pipeline \
            --output text \
            --no-paginate \
            --query 'imageDetails[].imageTags'
    '''
    fail_message = 'could not retrieve ECR image info'
    result = aws_command(command, fail_message)
    tag_lists = [result.stdout.rstrip().split()]
    tags = {tag for tag_list in tag_lists for tag in tag_list}
    if ecr_image_tag not in tags:
        log.render(log.ftext('\nerror: could not find requested image tag, found:', c='red'))
        for tag in tags:
            log.render(f'\t{tag}')
        sys.exit(1)


def aws_command(command, fail_message):
    # Remove excessive whitespace/newlines so that we can append --region
    command_full = f'{command.rstrip()} --region {region}'
    result = subprocess.run(
        command_full,
        shell=True,
        capture_output=True,
        encoding='utf-8'
    )
    if result.returncode != 0:
        log.render(log.ftext(f'\nerror: {fail_message}:', c='red'))
        log.render(f'command: {command_full}')
        log.render(f'stdout: {result.stdout}')
        log.render(f'stderr: {result.stderr}')
        sys.exit(1)
    return result
