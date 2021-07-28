# All regexes for file matching are non-recursive and regex parts (as separated by '/') are applied
# only at the appropriately directory depth, relative to provided parent directory.
#
# For example the regex 'subdir_a/subdir_b/.+file_suffix.vfc.gz$' has three parts: (1) 'subdir_a',
# (2) 'subdir_b', and (3) '.+file_suffix.vfc.gz$'. For a given parent directory, regex part (1) is
# only applied to all immediate subdir/files. The immediate subdirs/content of directories that
# match part (1) will similarly be searched using part (2). This process continues until all regex
# parts have been exhausted or there are no remaining directories to recurse into.


RUN_TYPE = 'umccrise'

DATA_SOURCES = {
    'cpsr': 'small_variants/.+-germline.predispose_genes.vcf.gz$',
    'pcgr': 'small_variants/.+somatic-PASS.vcf.gz$',
    'manta': 'structural/.+-manta.vcf.gz$',
    'purple': 'purple/.+.purple.cnv.gene.tsv$',
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
    'small_variants$': 10,
    'structural$': 10,
    'purple$': 10,
    '.+_cancer_report.html$': 5,
    'coverage$': 5,
    'log/data_versions.txt$': 5,
    'oncoviruses$': 5,
    'pierian$': 5,
    '.+-multiqc_report.html$': 2,
    '.+-multiqc_report_data$': 2,
    '.+-normal.cacao.html$': 2,
    '.+-normal.cpsr.html$': 2,
    '.+-somatic.pcgr.html$': 2,
    '.+-tumor.cacao.html$': 2,
    'cancer_report_tables$': 2,
}


def get_sample_name(dirpath):
    return dirpath.name
