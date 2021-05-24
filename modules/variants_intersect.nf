process module_variants_intersect {
  publishDir "${params.output_dir}/2_variants_intersect/${sample_name}"

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_type), path(vcf_one), path(index_one), path(vcf_two), path(index_two)

  output:
  tuple val(vcf_type), val(sample_name), path('*vcf')

  script:
  sample_name = "intersect__${vcf_one.getSimpleName()}__${vcf_two.getSimpleName()}"
  """
  bcftools isec "${vcf_one}" "${vcf_two}" -p ./
  """
}
