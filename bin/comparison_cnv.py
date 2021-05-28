#!/usr/bin/env python3
import argparse
import pathlib
import textwrap


import shared


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tsv_1', required=True, type=pathlib.Path,
            help='Input TSV (one) filepath')
    parser.add_argument('--tsv_2', required=True, type=pathlib.Path,
            help='Input TSV (two) filepath')
    args = parser.parse_args()
    if not args.tsv_1.exists():
        parser.error(f'Input file {args.tsv_1} does not exist')
    if not args.tsv_2.exists():
        parser.error(f'Input file {args.tsv_2} does not exist')
    return args


def main():
    # Get command line arguments
    args = get_arguments()

    # Run process
    woofr_source_fp = shared.get_woofr_source_fp()
    rscript = textwrap.dedent(f'''
        source('{woofr_source_fp}')
        compare_purple_gene_files(
            '{args.tsv_1}',
            '{args.tsv_2}',
            'cn_diff.tsv',
            'cn_diff_coord.tsv'
        )
    ''')
    shared.execute_command(f'R --vanilla <<EOF\n{rscript}\nEOF')


if __name__ == '__main__':
    main()
