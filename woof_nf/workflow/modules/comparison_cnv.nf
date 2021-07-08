process module_cnv_comparison {
  publishDir "${params.output_dir}/${attributes_in.sample_name}/copy_number_variants/"

  input:
  tuple val(attributes_in), path('1.tsv'), path('2.tsv')

  output:
  path('cn_diff.tsv')
  path('cn_diff_coord.tsv')

  script:
  """
  comparison_cnv.py \
    --tsv_1 1.tsv \
    --tsv_2 2.tsv
  """
}
