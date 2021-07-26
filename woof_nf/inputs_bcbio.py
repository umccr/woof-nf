import glob
import pathlib
import re


RUN_TYPE = 'bcbio'

DATA_SOURCES = {
    'ensemble': ['*-germline-ensemble-annotated.vcf.gz'],
    'gatk': ['*-germline-gatk-haplotype-annotated.vcf.gz'],
    'strelka2': ['*-germline-strelka2-annotated.vcf.gz'],
    'vardict': ['*-germline-vardict-annotated.vcf.gz'],
}

DATA_TYPES = {
    'ensemble': 'small_variants',
    'gatk': 'small_variants',
    'strelka2': 'small_variants',
    'vardict': 'small_variants',
}

COLUMN_NAME_MAPPING = {
    'ensemble': 'Ensemble',
    'gatk': 'GATK',
    'strelka2': 'Strelka2',
    'vardict': 'VarDict',
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


def get_sample_name(dirpath):
    sample_name_re = re.compile(r'^[\d_-]+T\d{4}_(.+?)(?:-merged)?$')
    return sample_name_re.match(dirpath.name).group(1)
