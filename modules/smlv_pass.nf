process module_smlv_pass {
  publishDir "${params.output_dir}/${sample_name}/small_variants/1_filtered_vcfs/"

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(sample_name), val(vcf_type), val(flags_in), path(vcf)

  output:
  tuple val(sample_name), val(vcf_type), val(flags_out), path('*.vcf.gz')

  script:
  // Unset has_index and set not filtered flag
  flags_out = (flags_in & ~FlagBits.INDEXED)
  flags_out = (flags_out ^ FlagBits.FILTERED)
  run = (flags_in & FlagBits.PTWO) ? 'second' : 'first'
  filename = "${vcf_type}__${run}__filtered__${vcf.getSimpleName()}"
  """
  {
    bcftools view -h "${vcf}";
    bcftools view -Hf .,PASS "${vcf}" | sort -k1,1V -k2,2n;
  } | \
    bcftools view -Oz \
    > "${filename}.vcf.gz"
  """
}
