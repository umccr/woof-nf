#!/usr/bin/env python3
import argparse
import glob
import pathlib
import textwrap
import subprocess
import sys


import log
import dependencies


umccrise_inputs = {
    'cpsr': ['small_variants', '-germline.predispose_genes.vcf.gz'],
    'pcgr': ['small_variants', '-somatic-PASS.vcf.gz'],
    'manta': ['structural', '-manta.vcf.gz'],
    'purple': ['purple', '.purple.cnv.gene.tsv']
}

file_types = {
    'cpsr': 'small_variants',
    'pcgr': 'small_variants',
    'manta': 'structural_variants',
    'purple': 'copy_number_variants'
}


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run_dir_one', required=True, nargs='+', type=pathlib.Path,
            help='Space separated list of run directories')
    parser.add_argument('--run_dir_two', required=True, nargs='+', type=pathlib.Path,
            help='Space separated list of run directories')
    parser.add_argument('--output_dir', required=True, type=pathlib.Path,
            help='Output directory')
    return parser.parse_args()


def check_arguments(args):
    log.task_msg_title('Checking arguments')
    log.task_msg_body('Not yet implemented - hold on to your seats!\n')
    log.render('Free pass for now :)\n')


def main():
    # TODO: splash

    # Print entry
    # TODO: further description on what will be done
    msg_body_text = (
        'Welcome to the UMCCR comparison pipeline\n'
    )
    log.task_msg_title('Starting comparison pipeline')
    log.task_msg_body(msg_body_text)

    # TODO: more version elsewhere
    # TODO: allow user to set threads
    import multiprocessing
    log.render(log.ftext(f'Command: {" ".join(sys.argv)}\n', f='bold'))
    log.render('Info:')
    log.render('  version: 0.0.1-alpha')
    log.render(f'  threads: {multiprocessing.cpu_count()}\n')

    # Get and check command line arguments
    args = get_arguments()
    check_arguments(args)

    # Check dependencies
    dependencies.check()

    # Get inputs and write to file
    input_list = get_inputs(args.run_dir_one, args.run_dir_two)
    inputs_fp = write_inputs(input_list, args.output_dir / 'input_files.tsv')

    # Execute pipeline
    run_pipeline(inputs_fp, args.output_dir)

    # Render report
    render_report(args.output_dir)

    # Exit message
    log.task_msg_title('Pipeline completed sucessfully! Goodbye')


def get_inputs(dir_one, dir_two):
    # Log directories to be searched
    log.task_msg_title('Discovering input files')
    log.render('\nDirectories searched:')
    log_input_directories(dir_one, '1')
    log_input_directories(dir_two, '2')
    log.render_newline()
    # Discover all inputs
    inputs_one = discover_run_files(dir_one)
    inputs_two = discover_run_files(dir_two)

    # Match samples between runs and also input files
    samples_matched, inputs_matched = match_inputs(inputs_one, inputs_two)
    # Create and render table displaying results
    matched_table = create_matched_table(inputs_one, inputs_two, samples_matched)
    samples_all = set(inputs_one) | set(inputs_two)
    log.render(f'Matched {len(samples_matched)} of {len(samples_all)} samples:')
    render_matched_table(matched_table)
    return inputs_matched


def create_matched_table(inputs_one, inputs_two, samples_matched):
    # NOTE: assuming all umccrise files; refactor will be required for extending to bcbio.
    #       I will want to have separate sections for umccrise and bcbio match tables
    file_columns = list(file_types.keys())
    # Define symbols
    tick_green = log.ftext('✓', c='green')
    tick_grey = log.ftext('✓', c='black')
    cross = log.ftext('⨯', c='red')
    # Create rows for matched pairs
    rows = list()
    for sample in sorted(samples_matched):
        # Only have sample appear on first line for matched pairs
        row_one = [sample, '1', tick_green]
        row_two = ['', '2', '']
        for file_type in file_columns:
            exist_one = file_type in inputs_one[sample]
            exist_two = file_type in inputs_two[sample]
            # Set symbol and symbol colour
            if exist_one and not exist_two:
                sym_one = tick_grey
                sym_two = cross
            elif not exist_one and exist_two:
                sym_one = cross
                sym_two = tick_grey
            elif exist_one and exist_two:
                sym_one = sym_two = tick_green
            elif not exist_one and not exist_two:
                sym_one = sym_two = cross
            row_one.append(sym_one)
            row_two.append(sym_two)
        rows.append((row_one, row_two))
    # Create rows for samples without matches
    samples_no_matched = samples_matched ^ (set(inputs_one) | set(inputs_two))
    for sample in samples_no_matched:
        # Get appropriate set
        row = [log.ftext(sample, c='red')]
        if sample in inputs_one:
            inputs = inputs_one
            row.append('1')
        elif sample in inputs_two:
            inputs = inputs_two
            row.append('2')
        # Cross to indicate match status
        row.append(cross)
        for file_type in file_columns:
            row.append(tick_green if file_type in inputs[sample] else cross)
        rows.append((row, ))
    return rows


def render_matched_table(rows):
    # Set header
    file_name_mapping = {
        'cpsr': 'CPSR',
        'pcgr': 'PCGR',
        'manta': 'Manta',
        'purple': 'PURPLE',
    }
    file_columns = [file_name_mapping[n] for n in file_types.keys()]
    header_tokens = ('Sample name', 'Set', 'Matched', *file_columns)
    # Min file column width; then set to header token
    # Get column sizes
    largest_sample = max(len(r[0]) for rs in rows for r in rs)
    csize_first = largest_sample + (4 - largest_sample % 4)
    csizes = [csize_first]
    for file_type in ['Set', 'Matched', *file_columns]:
        # Subtracting one for left-dominant centering on even lengths
        if len(file_type) < 8:
            csizes.append(8 - 1)
        else:
            csize = len(file_type) + (4 - len(file_type) % 4) - 1
            csizes.append(csize)
    # Render header
    log.render('  ', end='')
    for token, csize in zip(header_tokens, csizes):
        log.render(log.ftext(token.center(csize), f='underline'), end='')
    log.render_newline()
    # Render rows
    for row_set in rows:
        for row in row_set:
            # Adjust csize padding to account for ansi escape codes
            # NOTE: some further considerations may be required here when log.ANSI_CODES = False
            row_just = list()
            column_number = 0
            for csize, text in zip(csizes, row):
                # Exclude second matched sample name from table; replace with empty space
                column_number += 1
                ansi_ec_size = len(text) - len(log.ANSI_ESCAPE.sub('', text))
                csize += ansi_ec_size
                if column_number == 1:
                    row_just.append(text.ljust(csize))
                else:
                    row_just.append(text.center(csize))
            row_text = ''.join(row_just)
            log.render('  ' + row_text)
    log.render_newline()


def log_input_directories(dirpaths, n):
    log.render(f'  set {n}:')
    for dirpath in dirpaths:
        log.render(f'    {dirpath}')


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

    # Check matched samples for matching inputs
    inputs_matched = list()
    for sample_name in samples_matched:
        # Check and warn for missing inputs
        files_one = set(inputs_one[sample_name].keys())
        files_two = set(inputs_two[sample_name].keys())
        compare_items(files_one, files_two, 'file', f' in {sample_name}')
        # Push matches into new variable
        files_matched = files_one & files_two
        for file_source in files_matched:
            file_type = file_types[file_source]
            inputs_matched.extend((
                (sample_name, file_type, file_source, 'first', inputs_one[sample_name][file_source]),
                (sample_name, file_type, file_source, 'second', inputs_two[sample_name][file_source])
            ))
    return samples_matched, inputs_matched


def compare_items(a, b, item_name, extra=''):
    no_match = a ^ b
    if no_match and log.VERBOSITY >= 3:
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


def write_inputs(input_list, output_fp):
    # Create output directory if it does not already exist
    output_dir = output_fp.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    # Write file
    header_tokens  = ('sample_name', 'file_type', 'file_source', 'run_number', 'filepath')
    inputs_fp = pathlib.Path(output_fp)
    with inputs_fp.open('w') as fh:
        print(*header_tokens, sep='\t', file=fh)
        for input_entry in input_list:
            print(*input_entry, sep='\t', file=fh)
    return inputs_fp


def run_pipeline(inputs_fp, output_dir):
    # Start
    log.task_msg_title('Executing workflow')
    p = subprocess.Popen(
        f'./pipeline.nf --inputs_fp {inputs_fp} --output_dir {output_dir}',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        shell=True,
        universal_newlines=True,
    )
    # Stream output to terminal, replicating behaviour
    log.render('\nNextflow output:')
    # Print initial block (block delimiter as an empty newline)
    displayed_lines = 0
    for line in p.stdout:
        if line == '\n':
            break
        sys.stdout.write(f'    {line}')
        displayed_lines += 1
    sys.stdout.write('\n')
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
            print(''.join(lines))
            lines_rewrite = len(lines) + 1
            lines = list()
        else:
            # In block
            lines.append(f'    {line}')
    # Block until pipeline process exits
    p.wait()


def render_report(output_dir):
    log.task_msg_title('Rendering RMarkdown report')
    log.render_newline()
    output_fp = output_dir / 'report.html'
    rscript = textwrap.dedent(f'''
        library(rmarkdown)
        rmarkdown::render(
          'lib/report.Rmd',
          output_file='{output_fp.absolute()}',
          params=list(
            results_directory='{output_dir.absolute()}'
          )
        )
    ''')
    p = subprocess.run(
        f'R --vanilla <<EOF\n{rscript}\nEOF',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        encoding='utf-8'
    )
    if p.returncode != 0:
        log.render(f'error:\n{p.stderr}')
        sys.exit(1)


if __name__ == '__main__':
    main()
