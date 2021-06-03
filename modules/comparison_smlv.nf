process module_smlv_comparison {
  publishDir "${params.output_dir}/small_variants/3_comparison/", saveAs: { "${file_type}${fn_suffix}.tsv" }

  input:
  tuple val(file_type), val(flags), path(vcf_1), path(vcf_2), path(vcf_3)

  output:
  path('*.tsv')

  script:
  source = (flags & FlagBits.FILTERED) ? 'all' : 'filtered'
  fn_suffix = (source == 'filtered') ? '_filtered' : ''
  """
  comparison_smlv.py \
    --file_type "${file_type}" \
    --source "${source}" \
    --vcf_1 "${vcf_1}" \
    --vcf_2 "${vcf_2}" \
    --vcf_3 "${vcf_3}"
  """
}
