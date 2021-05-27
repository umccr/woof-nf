#!/usr/bin/env python3
import argparse
import pathlib


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vcf_1', required=True, type=pathlib.Path,
            help='Input VCF (one) filepath')
    parser.add_argument('--vcf_2', required=True, type=pathlib.Path,
            help='Input VCF (two) filepath')
    args = parser.parse_args()
    if not args.vcf_1.exists():
        parser.error(f'Input file {args.vcf_1} does not exist')
    if not args.vcf_2.exists():
        parser.error(f'Input file {args.vcf_2} does not exist')
    return args


def main():
    # Get command line arguments
    args = get_arguments()

    # Read in files and prepare data
    #   - woofr::manta_isec
    #     - rock::prep_manta_vcf
    #       - rock::read_manta_vcf
    #       - rock::.manta_proper_pairs
    # Make comparison
    #   - woofr::manta_isec_stats
    #   - woofr::get_circos
    # Write result


if __name__ == '__main__':
    main()
