process module_smlv_count {
  input:
  tuple val(attributes), path(vcf)

  output:
  tuple val(attributes), path('*tsv')

  script:
  source = attributes.filtered ? 'filtered' : 'input'
  """
  # Check for gzip magic bits
  magic_bits=\$(hexdump -n2 -e '2/1 "%02x" "\n"' ${vcf})
  if [[ "\${magic_bits}" == "1f8b" ]]; then
    variant_count=\$(gzip -cd "${vcf}" | sed '/^#/d' | wc -l)
  else
    variant_count=\$(sed '/^#/d' "${vcf}" | wc -l)
  fi;
  # Appropriately set run value
  if [[ "${attributes.file_source}" =~ __intersect\$ ]]; then
    run_value='n/a'
  else
    run_value="${attributes.position}"
  fi
  filename=\$(md5sum < ${vcf} | cut -f1 -d' ')
  echo -e "${attributes.file_source}\t${vcf.getSimpleName()}\t\${run_value}\t${source}\t\${variant_count}" > "\${filename}.tsv"
  """
}
