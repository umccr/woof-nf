process module_index_vcf {
  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_type), val(vcf_position), path(vcf)

  output:
  tuple val(vcf_type), val(vcf_position), path('*.tbi')

  script:
  """
  tabix "${vcf}"
  """
}
