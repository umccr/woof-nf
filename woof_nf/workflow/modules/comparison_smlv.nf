process module_smlv_comparison {
  publishDir "${publish_dir}", saveAs: { "${attributes_in.data_source}${fn_suffix}.tsv" }

  input:
  tuple val(attributes_in), path(vcf_0), path(vcf_1), path(vcf_2)

  output:
  path('*.tsv'), emit: comparison

  script:
  publish_basedir = "${params.output_dir}/${attributes_in.sample_name}"
  publish_dir = "${publish_basedir}/${attributes_in.run_type}/small_variants/3_comparison/"
  subset = attributes_in.filtered ? 'filtered' : 'pass'
  fn_suffix = attributes_in.filtered ? '_filtered' : ''
  """
  comparison_smlv.py \
    --sample_name "${attributes_in.sample_name}" \
    --file_type "${attributes_in.data_source}" \
    --source "${subset}" \
    --vcf_1 "${vcf_0}" \
    --vcf_2 "${vcf_1}" \
    --vcf_3 "${vcf_2}"
  """
}
