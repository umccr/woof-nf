process module_index_vcf {
  publishDir "${publish_dir}", pattern: '*.tbi'

  input:
  tuple val(attributes), path(vcf)

  output:
  tuple val(attributes), path(vcf), path('*.tbi')

  script:
  publish_dir = "${params.output_dir}/${attributes.sample_name}/small_variants/1_filtered_vcfs/"
  attributes.indexed = true
  """
  tabix "${vcf}"
  """
}
