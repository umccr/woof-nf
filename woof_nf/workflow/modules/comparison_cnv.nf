process module_cnv_comparison {
  publishDir "${publish_dir}"

  input:
  tuple val(attributes_in), path('1.tsv'), path('2.tsv')

  output:
  path('cn_diff.tsv'), emit: cn_diff
  path('cn_diff_coord.tsv'), emit: cn_diff_coord

  script:
  publish_basedir = "${params.output_dir}/${attributes_in.sample_name}"
  publish_dir = "${publish_basedir}/${attributes_in.run_type}/copy_number_variants/"
  """
  comparison_cnv.py \
    --tsv_1 1.tsv \
    --tsv_2 2.tsv
  """
}
