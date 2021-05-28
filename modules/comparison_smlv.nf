process module_smlv_comparison {
  publishDir "${params.output_dir}/small_variants/3_comparison/"

  input:
  tuple val(file_type), path(vcf_1), path(vcf_2), path(vcf_3)

  output:
  path('*.tsv')

  script:
  """
  comparison_smlv.py \
    --file_type "${file_type}" \
    --vcf_1 "${vcf_1}" \
    --vcf_2 "${vcf_2}" \
    --vcf_3 "${vcf_3}"
  """
}