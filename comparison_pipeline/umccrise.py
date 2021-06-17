import glob
import pathlib


from . import inputs
from . import log


source = 'umccrise'

inputs_list = {
    'cpsr': ['small_variants', '-germline.predispose_genes.vcf.gz'],
    'pcgr': ['small_variants', '-somatic-PASS.vcf.gz'],
    'manta': ['structural', '-manta.vcf.gz'],
    'purple': ['purple', '.purple.cnv.gene.tsv'],
}

file_types = {
    'cpsr': 'small_variants',
    'pcgr': 'small_variants',
    'manta': 'structural_variants',
    'purple': 'copy_number_variants',
}

column_name_mapping = {
    'cpsr': 'CPSR',
    'pcgr': 'PCGR',
    'manta': 'Manta',
    'purple': 'PURPLE',
}


def process_input_directory(dirpath, run):
    # source -> InputFile
    directory_inputs = list()
    for input_name, (subdir, suffix) in inputs_list.items():
        # Construct full glob expression, iterate matches
        glob_expr = str(dirpath / f'**/{subdir}/*{suffix}')
        for input_fp_str in glob.glob(glob_expr, recursive=True):
            input_fp = pathlib.Path(input_fp_str)
            sample_name = input_fp.parts[-3]
            # Create input file and record
            input_file = inputs.InputFile(
                sample_name,
                run,
                input_fp,
                input_name,
                file_types[input_name],
                source
            )
            directory_inputs.append(input_file)
    return directory_inputs
