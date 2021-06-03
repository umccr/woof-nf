#!/usr/bin/env python3
import argparse
import pathlib
import textwrap


import shared


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample_name', required=True, type=str,
            help='Sample name')
    parser.add_argument('--file_source', required=True, type=str,
            help='File source')
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

    # Run process
    woofr_source_fp = shared.get_woofr_source_fp()
    rscript = textwrap.dedent(f'''
        source('{woofr_source_fp}')
        v.isec <- manta_isec(
            '{args.vcf_1}',
            '{args.vcf_2}',
            '{args.sample_name}',
            '{args.file_source}'
        )
        v.stats <- manta_isec_stats(
            v.isec,
            '{args.sample_name}',
            '{args.file_source}'
        )
        get_circos(
            v.isec,
            '{args.sample_name}',
            './circos/'
        )
        v.fpfn <- dplyr::bind_rows(
            v.isec[c('fp', 'fn')],
            .id='FP_or_FN'
        )
        utils::write.table(
            v.stats,
            file=file.path('./', 'eval_metrics.tsv'),
            quote=FALSE,
            sep='\t',
            row.names=FALSE,
            col.names=TRUE
        )
        utils::write.table(
            v.fpfn,
            file=file.path('./', 'fpfn.tsv'),
            quote=FALSE,
            sep='\t',
            row.names=FALSE,
            col.names=TRUE
        )
    ''')
    shared.execute_command(f'R --vanilla <<EOF\n{rscript}\nEOF')


if __name__ == '__main__':
    main()
