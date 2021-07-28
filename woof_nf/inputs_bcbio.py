# See note in inputs_umccrise.py regarding file matching regexes.


import re


RUN_TYPE = 'bcbio'

DATA_SOURCES = {
    'tumour-ensemble': '(?<!germline)-ensemble-annotated.vcf.gz$',
    'normal-ensemble': '.+-germline-ensemble-annotated.vcf.gz$',
    'normal-gatk': '.+-germline-gatk-haplotype-annotated.vcf.gz$',
    'normal-strelka2': '.+-germline-strelka2-annotated.vcf.gz$',
    'normal-vardict': '.+-germline-vardict-annotated.vcf.gz$',
}

DATA_TYPES = {
    'tumour-ensemble': 'small_variants',
    'normal-ensemble': 'small_variants',
    'normal-gatk': 'small_variants',
    'normal-strelka2': 'small_variants',
    'normal-vardict': 'small_variants',
}

COLUMN_NAME_MAPPING = {
    'tumour-ensemble': 'Ensemble (tumour)',
    'normal-ensemble': 'Ensemble (normal)',
    'normal-gatk': 'GATK (normal)',
    'normal-strelka2': 'Strelka2 (normal)',
    'normal-vardict': 'VarDict (normal)',
}

FINGREPRINT_SCORE_THRESHOLD = 30

DIRECTORY_FINGERPRINT = {
    'bcbio-nextgen-commands.log$': 10,
    'bcbio-nextgen.log$': 10,
    'project-summary.yaml$': 10,
    'data_versions.csv$': 3,
    'metadata.csv$': 3,
    'multiqc$': 3,
    'programs.txt$': 3,
}


def get_sample_name(dirpath):
    sample_name_re_str = r'''
        # Leading timestamp
        ^[\d_-]+T\d{4}

        # Parts sometimes present
        (?:_Cromwell_WGS)?
        (?:_All_WGS)?
        (?:_\d{4}_\d{3}_\d{2})?

        # Sample name
        _(.+?)

        # Trailing token
        (?:-merged)?$
    '''
    sample_name_re = re.compile(sample_name_re_str, re.VERBOSE)
    return sample_name_re.match(dirpath.name).group(1)
