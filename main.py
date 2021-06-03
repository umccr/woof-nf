#!/usr/bin/env python3
import argparse
import glob
import pathlib
import subprocess
import sys


umccrise_inputs = {
    'cpsr': ['small_variants', '-germline.predispose_genes.vcf.gz'],
    'pcgr': ['small_variants', '-somatic-PASS.vcf.gz'],
    'manta': ['structural', '-manta.vcf.gz'],
    'purple': ['purple', '.purple.cnv.gene.tsv']
}


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run_dir_one', required=True, nargs='+', type=pathlib.Path,
            help='Space separated list of run directories')
    parser.add_argument('--run_dir_two', required=True, nargs='+', type=pathlib.Path,
            help='Space separated list of run directories')
    return parser.parse_args()


def check_arguments(args):
    pass


def main():
    # Get and check command line arguments
    args = get_arguments()
    check_arguments(args)

    # Get inputs and write to file
    input_list = get_inputs(args.run_dir_one, args.run_dir_two)
    input_fp = pathlib.Path('testing/inputs.tsv')
    with input_fp.open('w') as fh:
        for input_entry in input_list:
            print(*input_entry, sep='\t', file=fh)

    # Execute pipeline
    run_pipeline(input_fp)


def get_inputs(dir_one, dir_two):
    # Discover all inputs
    inputs_one = discover_run_files(dir_one)
    inputs_two = discover_run_files(dir_two)
    # Match samples between runs and also input files
    return match_inputs(inputs_one, inputs_two)


def discover_run_files(dirpaths):
    input_collection = dict()
    for dirpath in dirpaths:
        # Discover files for each input directory
        directory_inputs = process_input_directory(dirpath)
        # Merge input files with return variable - samples should only exist in one input dir
        for sample_name, sample_inputs in directory_inputs.items():
            assert sample_name not in input_collection
            input_collection[sample_name] = sample_inputs
    return input_collection


def process_input_directory(dirpath):
    # sample_name -> input_name -> input_fp
    directory_inputs = dict()
    for input_name, (subdir, suffix) in umccrise_inputs.items():
        # Construct full glob expression, iterate matches
        glob_expr = str(dirpath / f'**/{subdir}/*{suffix}')
        for input_fp_str in glob.glob(glob_expr, recursive=True):
            # NOTE: obtaining sample name here is specific to Umccrise output
            input_fp = pathlib.Path(input_fp_str)
            sample_name = input_fp.parts[-3]
            # TODO: remove version clipping - dev only
            sample_name = sample_name.split('__')[1]
            if sample_name not in directory_inputs:
                directory_inputs[sample_name] = dict()
            directory_inputs[sample_name][input_name] = input_fp
    return directory_inputs


def match_inputs(inputs_one, inputs_two):
    # Check for missing samples
    samples_one = set(inputs_one.keys())
    samples_two = set(inputs_two.keys())
    compare_items(samples_one, samples_two, 'sample')
    samples_matched = samples_one & samples_two
    print(f'info: matched {len(samples_matched)} samples', file=sys.stderr)

    # Check matched samples for matching inputs
    inputs_matched = list()
    for sample_name in samples_matched:
        # Check and warn for missing inputs
        files_one = set(inputs_one[sample_name].keys())
        files_two = set(inputs_two[sample_name].keys())
        compare_items(files_one, files_two, 'file', f' in {sample_name}')
        # Push matches into new variable
        files_matched = files_one & files_two
        for file_type in files_matched:
            inputs_matched.extend((
                (sample_name, file_type, 'first', inputs_one[sample_name][file_type]),
                (sample_name, file_type, 'second', inputs_two[sample_name][file_type])
            ))
    return inputs_matched


def compare_items(a, b, item_name, extra=''):
    no_match = a ^ b
    if no_match:
        plurality = f'{item_name}s' if len(no_match) > 1 else item_name
        msg = f'warning: no match found for {len(no_match)} {plurality}{extra}:'
        print(msg, file=sys.stderr)
        # Print set differences
        no_match_one = a.difference(b)
        no_match_two = b.difference(a)
        if no_match_one:
            nmatch_one_strs = [f'\t- {name} (first run only)' for name in no_match_one]
            print(*nmatch_one_strs, sep='\n', file=sys.stderr)
        if no_match_two:
            nmatch_two_strs = [f'\t- {name} (second run only)' for name in no_match_two]
            print(*nmatch_two_strs, sep='\n', file=sys.stderr)


def run_pipeline(input_fp):
    # Start
    p = subprocess.Popen(
        './pipeline.nf',
        f'--input_fp {input_fp}',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        shell=True,
        universal_newlines=True,
    )
    # Stream output to terminal, replicating behaviour
    # Print initial block (block delimiter as an empty newline)
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
            # End of block
            # Set cursor to first rewrite line
            sys.stdout.write(f'\u001b[{lines_rewrite}A')
            # Clear to end of terminal
            sys.stdout.write('\u001b[0J')
            # Write new lines, prepare for next block
            sys.stdout.write(''.join(lines))
            lines_rewrite = len(lines)
            lines = list()
        else:
            # In block
            lines.append(line)
    # Block until pipeline process exits
    p.wait()


if __name__ == '__main__':
    main()
