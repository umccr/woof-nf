process module_variants_intersect {
  publishDir "${params.output_dir}/2_variants_intersect/${source}/${vcf_type}"

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_type), val(flags), path('1.vcf.gz'), path('1.vcf.gz.tbi'), path('2.vcf.gz'), path('2.vcf.gz.tbi')

  output:
  tuple val(vcf_type), val(flags), path('*vcf')

  script:
  source = (flags & 0b0001) ? 'filtered' : 'input'
  """
  bcftools isec 1.vcf.gz 2.vcf.gz -p ./
  """
}
