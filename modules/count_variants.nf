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
  # Check for gzip magic bits
  magic_bits=\$(hexdump -n2 -e '2/1 "%02x" "\n"' ${vcf})
  if [[ "\${magic_bits}" == "1f8b" ]]; then
    variant_count=\$(gzip -cd "${vcf}" | sed '/^#/d' | wc -l)
  else
    variant_count=\$(sed '/^#/d' "${vcf}" | wc -l)
  fi;
  echo -e "${vcf_type}\t${vcf.getSimpleName()}\t${source}\t\${variant_count}" > "${filename}"
  """
}
