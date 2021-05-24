process module_count_variants {
  publishDir "${params.output_dir}/3_variant_counts/${subdir}"

  container 'public.ecr.aws/amazonlinux/amazonlinux:latest'

  input:
  tuple val(subdir), path(vcf)

  output:
  path('*tsv')

  script:
  """
  variant_count=\$(gzip -cd "${vcf}" | sed '/^##/d' | wc -l)
  echo -e "${vcf.getSimpleName()}\t\${variant_count}" > "${vcf.getSimpleName()}.tsv"
  """
}
