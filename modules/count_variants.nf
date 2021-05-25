process module_count_variants {
  container 'public.ecr.aws/amazonlinux/amazonlinux:latest'

  input:
  tuple val(vcf_type), val(flags), path(vcf)

  output:
  path('*tsv')

  script:
  source = (flags & FlagBits.FILTERED) ? 'input' : 'filtered'
  uuid = UUID.randomUUID().toString()
  filename = "${uuid}.tsv"
  """
  echo $task
  variant_count=\$(gzip -cd "${vcf}" | sed '/^##/d' | wc -l)
  echo -e "${vcf_type}\t${vcf.getSimpleName()}\t${source}\t\${variant_count}" > "${filename}"
  """
}
