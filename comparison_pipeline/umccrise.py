import glob
import pathlib


from . import inputs
from . import log


SOURCE = 'umccrise'

INPUTS_LIST = {
    'cpsr': ['small_variants', '-germline.predispose_genes.vcf.gz'],
    'pcgr': ['small_variants', '-somatic-PASS.vcf.gz'],
    'manta': ['structural', '-manta.vcf.gz'],
    'purple': ['purple', '.purple.cnv.gene.tsv'],
}

FILE_TYPES = {
    'cpsr': 'small_variants',
    'pcgr': 'small_variants',
    'manta': 'structural_variants',
    'purple': 'copy_number_variants',
}

COLUMN_NAME_MAPPING = {
    'cpsr': 'CPSR',
    'pcgr': 'PCGR',
    'manta': 'Manta',
    'purple': 'PURPLE',
}


def process_input_directory(dirpath, run):
    directory_inputs = list()
    for input_name, (subdir, suffix) in INPUTS_LIST.items():
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
                FILE_TYPES[input_name],
                SOURCE
            )
            directory_inputs.append(input_file)
    return directory_inputs
