process module_smlv_count {
  input:
  tuple val(sample_name), val(vcf_type), val(flags), path(vcf)

  output:
  tuple val(sample_name), path('*tsv')

  script:
  source = (flags & FlagBits.FILTERED) ? 'filtered' : 'input'
  run = (flags & FlagBits.PTWO) ? 'second' : 'first'
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
  # Appropriately set run value
  if [[ "${vcf_type}" =~ __intersect\$ ]]; then
    run_value='n/a'
  else
    run_value="${run}"
  fi
  echo -e "${vcf_type}\t${vcf.getSimpleName()}\t\${run_value}\t${source}\t\${variant_count}" > "${filename}"
  """
}
