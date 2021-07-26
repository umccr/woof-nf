process module_smlv_pass {
  publishDir "${params.output_dir}/${attributes_in.sample_name}/small_variants/1_filtered_vcfs/"

  input:
  tuple val(attributes_in), path(vcf)

  output:
  tuple val(attributes_out), path('*.vcf.gz')

  script:
  filename = "${attributes_in.data_source}__${attributes_in.run_type}__filtered__${vcf.getSimpleName()}"
  attributes_out = attributes_in.clone()
  attributes_out.indexed = false
  attributes_out.filtered = true
  """
  {
    bcftools view -h "${vcf}";
    bcftools view -Hf .,PASS "${vcf}" | sort -k1,1V -k2,2n;
  } | \
    bcftools view -Oz \
    > "${filename}.vcf.gz"
  """
}
