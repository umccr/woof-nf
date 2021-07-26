process module_smlv_count {
  input:
  tuple val(attributes_in), path(vcf)

  output:
  tuple val(attributes_out), path('*tsv')

  script:
  data_source = attributes_in.data_source
  filtered = attributes_in.filtered ? 'filtered' : 'pass'
  attributes_out = attributes_in.clone()
  """
  # Count variants and appropriately set run value
  variant_count=\$(bcftools view -H "${vcf}" | wc -l)
  if [[ "${attributes_in.data_source}" =~ __intersect\$ ]]; then
    run_value='n/a'
  else
    run_value="${attributes_in.run_number}"
  fi
  filename=\$(bcftools view -h ${vcf} | md5sum | cut -f1 -d' ')
  echo -e "${data_source}\t${vcf.getSimpleName()}\t\${run_value}\t${filtered}\t\${variant_count}" > "\${filename}.tsv"
  """
}
