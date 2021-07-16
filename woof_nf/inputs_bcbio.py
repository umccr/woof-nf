import glob
import pathlib


SOURCE = 'bcbio'

INPUTS_LIST = {
    'strelka2': ['*-germline-strelka2-annotated.vcf.gz'],
}

FILE_TYPES = {
    'strelka2': 'small_variants',
}

COLUMN_NAME_MAPPING = {
    'strelka2': 'Strelka2',
}

FINGREPRINT_SCORE_THRESHOLD = 30

DIRECTORY_FINGERPRINT = {
    'bcbio-nextgen-commands.log': 10,
    'bcbio-nextgen.log': 10,
    'project-summary.yaml': 10,
    'data_versions.csv': 3,
    'metadata.csv': 3,
    'multiqc': 3,
    'programs.txt': 3,
}


def is_dir_type(dirpath: pathlib.Path) -> bool:
    score = 0
    for glob_pattern, value in DIRECTORY_FINGERPRINT.items():
        if list(dirpath.glob(glob_pattern)):
            score += value
    return score >= FINGREPRINT_SCORE_THRESHOLD
