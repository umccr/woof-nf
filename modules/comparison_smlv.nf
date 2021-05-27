process module_smlv_comparison {
  publishDir "${params.output_dir}/small_variants/3_comparison/"

  input:
  tuple val(file_type), val(flags), path(vcf_1), path(vcf_2), path(vcf_3)

  output:
  path('result.tsv')

  script:
  """
  comparison_smlv.py --vcf_1 "${vcf_1}" --vcf_2 "${vcf_2}" --vcf_3 "${vcf_3}"
  touch result.tsv
  """
}
