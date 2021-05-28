import pathlib
import subprocess
import sys


def get_woofr_source_fp():
    return get_lib_path() / 'woofr_compare.R'


def get_lib_path():
    # Assume script path is in ./bin/ and library code is in ./lib/
    script_path = pathlib.Path(__file__).resolve()
    return (script_path.parent / '../lib').resolve()


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
