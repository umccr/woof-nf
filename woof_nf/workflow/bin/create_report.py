#!/usr/bin/env python3
import argparse
import pathlib
import textwrap


import shared


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', required=True, type=pathlib.Path,
            help='Input directory containing sample comparison data')
    parser.add_argument('--output_fp', required=True, type=pathlib.Path,
            help='Output filepath')
    args = parser.parse_args()
    if not args.input_dir.exists():
        parser.error(f'Input directory {args.input_dir} does not exist')
    if not args.output_fp.parent.exists():
        parser.error(f'Directory for output file {args.output_fp.parent} does not exist')
    return args


def main():
    # Get command line arguments
    args = get_arguments()
    report_dir = pathlib.Path(__file__).parent / 'report'
    rscript = textwrap.dedent(f'''
        library(rmarkdown)
        rmarkdown::render(
          '{report_dir / "report.Rmd"}',
          output_file='{args.output_fp.absolute()}',
          params=list(
            results_directory='{args.input_dir.absolute()}'
          )
        )
    ''')
    shared.execute_command(f'R --vanilla <<EOF\n{rscript}\nEOF')


if __name__ == '__main__':
    main()
