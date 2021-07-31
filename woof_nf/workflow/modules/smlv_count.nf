process module_smlv_count {
  input:
  tuple val(attributes_in), path(vcf)

  output:
  tuple val(attributes_out), path('*tsv')

  script:
  filtered = attributes_in.filtered ? 'filtered' : 'pass'
  run_number = attributes_in.run_number ? attributes_in.run_number : 'none'
  filename = "${attributes_in.data_source}__${run_number}__${filtered}__${vcf.getSimpleName()}"
  attributes_out = attributes_in.clone()
  """
  # Count variants and appropriately set run value
  variant_count=\$(bcftools view -H "${vcf}" | wc -l)
  echo -e "${attributes_in.data_source}\t${run_number}\t${filtered}\t\${variant_count}" > "${filename}.tsv"
  """
}
