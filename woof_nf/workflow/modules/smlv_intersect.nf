process module_smlv_intersect {
  publishDir "${publish_dir}"

  input:
  tuple val(attributes), path('1.vcf.gz'), path('1.vcf.gz.tbi'), path('2.vcf.gz'), path('2.vcf.gz.tbi')

  output:
  tuple val(attributes), path('*.vcf')

  script:
  source = attributes.filtered ? 'filtered' : 'input'
  publish_dir_base = "${params.output_dir}/${attributes.sample_name}/small_variants/2_variants_intersect/"
  publish_dir = "${publish_dir_base}/${source}/${attributes.file_source}"
  attributes.indexed = false
  """
  bcftools isec 1.vcf.gz 2.vcf.gz -p ./
  # Remove unneeded output VCF; NF output globbing doesn't allow exclusion at this level
  rm 0003.vcf
  """
}
