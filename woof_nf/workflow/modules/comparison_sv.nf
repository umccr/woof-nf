process module_sv_comparison {
  publishDir "${params.output_dir}/${attributes.sample_name}/structural_variants/"

  input:
  tuple val(attributes), path('1.vcf.gz'), path('2.vcf.gz')

  output:
  path('circos/*')
  path('eval_metrics.tsv')
  path('fpfn.tsv')

  script:
  """
  comparison_sv.py \
    --sample_name "${attributes.sample_name}" \
    --file_source "manta" \
    --vcf_1 1.vcf.gz \
    --vcf_2 2.vcf.gz
  """
}
