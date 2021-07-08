process module_smlv_pass {
  publishDir "${params.output_dir}/${attributes.sample_name}/small_variants/1_filtered_vcfs/"

  input:
  tuple val(attributes), path(vcf)

  output:
  tuple val(attributes), path('*.vcf.gz')

  script:
  attributes.indexed = false
  attributes.filtered = true
  filename = "${attributes.file_source}__${attributes.position}__filtered__${vcf.getSimpleName()}"
  """
  {
    bcftools view -h "${vcf}";
    bcftools view -Hf .,PASS "${vcf}" | sort -k1,1V -k2,2n;
  } | \
    bcftools view -Oz \
    > "${filename}.vcf.gz"
  """
}
