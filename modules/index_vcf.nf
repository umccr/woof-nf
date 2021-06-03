process module_index_vcf {
  publishDir "${params.output_dir}/${sample_name}/small_variants/1_filtered_vcfs/", pattern: '*.tbi'

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(sample_name), val(vcf_type), val(flags_in), path(vcf)

  output:
  tuple val(sample_name), val(vcf_type), val(flags_out), path(vcf), path('*.tbi')

  script:
  flags_out = flags_in ^ FlagBits.INDEXED
  """
  tabix "${vcf}"
  """
}
