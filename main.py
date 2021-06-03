#!/usr/bin/env python3
import argparse
import subprocess
import sys


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run_dir_one', required=True, nargs='+', type=str,
            help='Space separated list of run directories (can be globs)')
    parser.add_argument('--run_dir_two', required=True, nargs='+', type=str,
            help='Space separated list of run directories (can be globs)')
    return parser.parse_args()


def check_arguments(args):
    pass


def main():
    # Get and check command line arguments
    args = get_arguments()
    check_arguments(args)

    # Execute pipeline
    p = subprocess.Popen(
        './pipeline.nf',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        shell=True,
        universal_newlines=True,
    )

    # Print initial block
    displayed_lines = 0
    for line in p.stdout:
        if line == '\n':
            break
        sys.stdout.write(line)
        displayed_lines += 1
    lines_rewrite = displayed_lines - 2

    # For each new block, rewrite all but first two lines
    lines = list()
    for line in p.stdout:
        if line == '\n':
            # Set cursor to first rewrite line
            sys.stdout.write(f'\u001b[{lines_rewrite}A')
            # Clear to end of terminal
            sys.stdout.write('\u001b[0J')
            # Write new lines
            sys.stdout.write(''.join(lines))
            lines_rewrite = len(lines)
            lines = list()
        else:
            lines.append(line)
    p.wait()


if __name__ == '__main__':
    main()
