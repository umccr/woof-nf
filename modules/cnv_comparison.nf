process module_cnv_comparison {
  publishDir "${params.output_dir}/copy_number_variants/"

  input:
  tuple path('1.tsv'), path('2.tsv')

  output:
  path('result.tsv')

  script:
  """
  cnv_comparison.py --tsv_1 1.tsv --tsv_2 2.tsv
  touch result.tsv
  """
}
