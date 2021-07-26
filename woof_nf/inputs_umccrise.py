import glob
import pathlib


RUN_TYPE = 'umccrise'

DATA_SOURCES = {
    'cpsr': ['small_variants', '*-germline.predispose_genes.vcf.gz'],
    'pcgr': ['small_variants', '*-somatic-PASS.vcf.gz'],
    'manta': ['structural', '*-manta.vcf.gz'],
    'purple': ['purple', '*.purple.cnv.gene.tsv'],
}

DATA_TYPES = {
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

FINGREPRINT_SCORE_THRESHOLD = 30

DIRECTORY_FINGERPRINT = {
    'small_variants': 10,
    'structural': 10,
    'purple': 10,
    '*_cancer_report.html': 5,
    'coverage': 5,
    'log/data_versions.txt': 5,
    'oncoviruses': 5,
    'pierian': 5,
    '*-multiqc_report.html': 2,
    '*-multiqc_report_data': 2,
    '*-normal.cacao.html': 2,
    '*-normal.cpsr.html': 2,
    '*-somatic.pcgr.html': 2,
    '*-tumor.cacao.html': 2,
    'cancer_report_tables': 2,
}


def is_dir_type(dirpath: pathlib.Path) -> bool:
    score = 0
    for glob_pattern, value in DIRECTORY_FINGERPRINT.items():
        if list(dirpath.glob(glob_pattern)):
            score += value
    return score >= FINGREPRINT_SCORE_THRESHOLD


def get_sample_name(dirpath):
    return dirpath.name
