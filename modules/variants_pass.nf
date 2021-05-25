process module_variants_pass {
  publishDir "${params.output_dir}/1_variants_pass/"

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_type), val(flags_in), path(vcf)

  output:
  tuple val(vcf_type), val(flags_out), path('*.vcf.gz')

  script:
  // Unset has_index and set not filtered flag
  flags_out = (flags_in & ~FlagBits.INDEXED)
  flags_out = (flags_out ^ FlagBits.FILTERED)
  def sample_name = vcf.getSimpleName()
  """
  {
    bcftools view -h "${vcf}";
    bcftools view -Hf .,PASS "${vcf}" | sort -k1,1V -k2,2n;
  } | \
    bcftools view -Oz \
    > "${sample_name}_pass.vcf.gz"
  """
}
