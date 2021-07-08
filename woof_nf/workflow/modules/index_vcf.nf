process module_index_vcf {
  publishDir "${publish_dir}", pattern: '*.tbi'

  input:
  tuple val(attributes_in), path(vcf)

  output:
  tuple val(attributes_out), path(vcf), path('*.tbi')

  script:
  publish_dir = "${params.output_dir}/${attributes_in.sample_name}/small_variants/1_filtered_vcfs/"
  attributes_out = attributes_in.clone()
  attributes_out.indexed = true
  """
  tabix "${vcf}"
  """
}
