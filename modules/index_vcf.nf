process module_index_vcf {
  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_type), val(flags_in), path(vcf)

  output:
  tuple val(vcf_type), val(flags_out), path(vcf), path('*.tbi')

  script:
  // Index has_index flat
  flags_out = flags_in ^ 0b0100
  """
  tabix "${vcf}"
  """
}
