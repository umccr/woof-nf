import pathlib
import subprocess
import sys


def get_woofr_source_fp():
    return get_lib_path() / 'woofr_compare.R'


def get_lib_path():
    # Currently the nf-amazon plugin only uploads the ./bin/ directory to AWS instances. Any ./lib/
    # files accessed during task execution are required to be in ./bin/. The ./bin/ directory
    # appears as /nextflow-bin/ on AWS instances.
    return pathlib.Path(__file__).parent


def execute_command(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        encoding='utf-8'
    )
    if result.returncode != 0:
        print('Failed to run command:', result.args, file=sys.stderr)
        print('stdout:', result.stdout, file=sys.stderr)
        print('stderr:', result.stderr, file=sys.stderr)
        sys.exit(1)
    return result
