process module_cnv_comparison {
  publishDir "${params.output_dir}/copy_number_variants/"

  input:
  tuple path('1.tsv'), path('2.tsv')

  output:
  path('result.tsv')

  script:
  """
  touch result.tsv
  """
}
