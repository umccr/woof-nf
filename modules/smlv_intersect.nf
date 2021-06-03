process module_smlv_intersect {
  publishDir "${params.output_dir}/${sample_name}/small_variants/2_variants_intersect/${source}/${vcf_type}"

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(sample_name), val(vcf_type), val(flags), path('1.vcf.gz'), path('1.vcf.gz.tbi'), path('2.vcf.gz'), path('2.vcf.gz.tbi')

  output:
  tuple val(sample_name), val(vcf_type), val(flags), path('*.vcf')

  script:
  source = (flags & FlagBits.FILTERED) ? 'filtered' : 'input'
  """
  bcftools isec 1.vcf.gz 2.vcf.gz -p ./
  # Remove unneeded output VCF; NF output globbing doesn't allow exclusion at this level
  rm 0003.vcf
  """
}
