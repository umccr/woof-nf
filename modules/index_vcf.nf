process module_index_vcf {
  publishDir "${params.output_dir}/1_vcfs/", pattern: '*.tbi'

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_type), val(flags_in), path(vcf)

  output:
  tuple val(vcf_type), val(flags_out), path(vcf), path('*.tbi')

  script:
  flags_out = flags_in ^ FlagBits.INDEXED
  """
  tabix "${vcf}"
  """
}
