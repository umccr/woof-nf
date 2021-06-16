import glob
import pathlib


from . import inputs
from . import log


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
    # NOTE: once input streams have been generalised further this will need to be called in the
    # outer scope
    matched_table = inputs.create_matched_table(inputs_one, inputs_two, samples_matched)
    samples_all = set(inputs_one) | set(inputs_two)
    log.render(f'Matched {len(samples_matched)} of {len(samples_all)} samples:')
    inputs.render_matched_table(matched_table)
    return inputs_matched


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
