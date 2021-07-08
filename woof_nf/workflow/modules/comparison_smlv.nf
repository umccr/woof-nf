process module_smlv_comparison {
  publishDir "${publish_dir}", saveAs: { "${attributes_in.file_type}${fn_suffix}.tsv" }

  input:
  tuple val(attributes_in), path(vcf_0), path(vcf_1), path(vcf_2)

  output:
  path('*.tsv')

  script:
  publish_dir = "${params.output_dir}/${attributes_in.sample_name}/small_variants/3_comparison/"
  fn_suffix = (attributes_in.source == 'filtered') ? '_filtered' : ''
  """
  comparison_smlv.py \
    --sample_name "${attributes_in.sample_name}" \
    --file_type "${attributes_in.file_type}" \
    --source "${attributes_in.source}" \
    --vcf_1 "${vcf_0}" \
    --vcf_2 "${vcf_1}" \
    --vcf_3 "${vcf_2}"
  """
}
