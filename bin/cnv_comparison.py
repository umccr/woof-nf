#!/usr/bin/env python3
import argparse
import pathlib


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tsv_1', required=True, type=pathlib.Path,
            help='Input VCF (one) filepath')
    parser.add_argument('--tsv_2', required=True, type=pathlib.Path,
            help='Input VCF (two) filepath')
    args = parser.parse_args()
    if not args.tsv_1.exists():
        parser.error(f'Input file {args.tsv_1} does not exist')
    if not args.tsv_2.exists():
        parser.error(f'Input file {args.tsv_2} does not exist')
    return args


def main():
    # Get command line arguments
    args = get_arguments()

    # Read in files and prepare data
    # Make comparison
    # Write result


if __name__ == '__main__':
    main()
