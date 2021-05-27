process module_sv_comparison {
  publishDir "${params.output_dir}/structural_variants/"

  input:
  tuple path('1.vcf.gz'), path('2.vcf.gz')

  output:
  path('result.tsv')

  script:
  """
  sv_comparison.py --vcf_1 1.vcf.gz --vcf_2 2.vcf.gz
  touch result.tsv
  """
}
