process module_count_variants {
  container 'public.ecr.aws/amazonlinux/amazonlinux:latest'

  input:
  tuple val(vcf_type), val(flags), path(vcf)

  output:
  path('*tsv')

  script:
  source = (flags & 0b0001) ? 'input' : 'filtered'
  """
  echo $task
  variant_count=\$(gzip -cd "${vcf}" | sed '/^##/d' | wc -l)
  echo -e "${vcf_type}\t${vcf.getSimpleName()}\t${source}\t\${variant_count}" > "${vcf_type}_${source}_${task.index}.tsv"
  """
}
