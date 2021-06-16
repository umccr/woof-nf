#!/usr/bin/env python3
import argparse
import pathlib
import textwrap
import sys


import shared


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample_name', required=True,
            help='Sample name')
    parser.add_argument('--file_type', required=True,
            help='Name of file type')
    parser.add_argument('--source', required=True,
            help='Source of variants (input or filtered)')
    parser.add_argument('--vcf_1', required=True, type=pathlib.Path,
            help='Input VCF (one) filepath')
    parser.add_argument('--vcf_2', required=True, type=pathlib.Path,
            help='Input VCF (two) filepath')
    parser.add_argument('--vcf_3', required=True, type=pathlib.Path,
            help='Input VCF (three) filepath')
    args = parser.parse_args()
    if not args.vcf_1.exists():
        parser.error(f'Input file {args.vcf_1} does not exist')
    if not args.vcf_2.exists():
        parser.error(f'Input file {args.vcf_2} does not exist')
    if not args.vcf_3.exists():
        parser.error(f'Input file {args.vcf_3} does not exist')
    return args


def main():
    # Get command line arguments
    args = get_arguments()

    # Import woof python code
    sys.path.insert(0, str(shared.get_lib_path()))
    import woof_compare

    # Run process
    woof_compare.eval(
        args.vcf_1,
        args.vcf_2,
        args.vcf_3,
        f'{args.file_type}.tsv',
        args.sample_name,
        args.file_type,
        args.source
    )


if __name__ == '__main__':
    main()
