process module_smlv_intersect {
  publishDir "${publish_dir}"

  input:
  tuple val(attributes_in), path('1.vcf.gz'), path('1.vcf.gz.tbi'), path('2.vcf.gz'), path('2.vcf.gz.tbi')

  output:
  tuple val(attributes_out), path('*.vcf.gz')

  script:
  source = attributes_in.filtered ? 'filtered' : 'input'
  publish_basedir = "${params.output_dir}/${attributes_in.sample_name}"
  publish_middir = "${attributes_in.run_type}/small_variants/2_variants_intersect"
  publish_dir = "${publish_basedir}/${publish_middir}/${source}/${attributes_in.data_source}"
  attributes_out = attributes_in.clone()
  attributes_out.indexed = false
  """
  bcftools isec 1.vcf.gz 2.vcf.gz -Oz -p ./
  # Remove unneeded output VCF; NF output globbing doesn't allow exclusion at this level
  rm 0003.vcf.gz
  """
}
