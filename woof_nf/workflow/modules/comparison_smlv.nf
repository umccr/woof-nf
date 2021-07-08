process module_smlv_comparison {
  publishDir "${publish_dir}", saveAs: { "${attributes.file_type}${fn_suffix}.tsv" }

  input:
  tuple val(attributes), path(vcf_0), path(vcf_1), path(vcf_2)

  output:
  path('*.tsv')

  script:
  publish_dir = "${params.output_dir}/${attributes.sample_name}/small_variants/3_comparison/"
  fn_suffix = (attributes.source == 'filtered') ? '_filtered' : ''
  """
  comparison_smlv.py \
    --sample_name "${attributes.sample_name}" \
    --file_type "${attributes.file_type}" \
    --source "${attributes.source}" \
    --vcf_1 "${vcf_0}" \
    --vcf_2 "${vcf_1}" \
    --vcf_3 "${vcf_2}"
  """
}
