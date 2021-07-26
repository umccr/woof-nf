process module_smlv_count {
  input:
  tuple val(attributes_in), path(vcf)

  output:
  tuple val(attributes_out), path('*tsv')

  script:
  file_source = attributes_in.file_source
  filtered = attributes_in.filtered ? 'filtered' : 'pass'
  attributes_out = attributes_in.clone()
  """
  # Count variants and sppropriately set run value
  variant_count=\$(bcftools view -H "${vcf}" | wc -l)
  if [[ "${attributes_in.file_source}" =~ __intersect\$ ]]; then
    run_value='n/a'
  else
    run_value="${attributes_in.position}"
  fi
  filename=\$(bcftools view -h ${vcf} | md5sum | cut -f1 -d' ')
  echo -e "${file_source}\t${vcf.getSimpleName()}\t\${run_value}\t${filtered}\t\${variant_count}" > "\${filename}.tsv"
  """
}
