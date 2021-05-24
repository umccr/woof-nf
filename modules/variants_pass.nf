process module_variants_pass {
  publishDir "${params.output_dir}/1_variants_pass/"

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_position), path(vcf)

  output:
  tuple val(vcf_position), path('*.vcf.gz')

  script:
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
