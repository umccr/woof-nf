process module_smlv_pass {
  publishDir "${publish_dir}"

  input:
  tuple val(attributes_in), path(vcf)

  output:
  tuple val(attributes_out), path('*.vcf.gz')

  script:
  publish_basedir = "${params.output_dir}/${attributes_in.sample_name}"
  publish_dir = "${publish_basedir}/${attributes_in.run_type}/small_variants/1_filtered_vcfs/"
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
