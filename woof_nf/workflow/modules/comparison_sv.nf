process module_sv_comparison {
  publishDir "${publish_dir}"

  input:
  tuple val(attributes_in), path('1.vcf.gz'), path('2.vcf.gz')

  output:
  path('circos/*')
  path('eval_metrics.tsv')
  path('fpfn.tsv')

  script:
  publish_basedir = "${params.output_dir}/${attributes_in.sample_name}"
  publish_dir = "${publish_basedir}/${attributes_in.run_type}/structural_variants/"
  """
  comparison_sv.py \
    --sample_name "${attributes_in.sample_name}" \
    --file_source "manta" \
    --vcf_1 1.vcf.gz \
    --vcf_2 2.vcf.gz
  """
}
