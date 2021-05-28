process module_sv_comparison {
  publishDir "${params.output_dir}/structural_variants/"

  input:
  tuple path('1.vcf.gz'), path('2.vcf.gz')

  output:
  path('circos/*')
  path('eval_metrics.tsv')
  path('fpfn.tsv')

  script:
  """
  comparison_sv.py \
    --vcf_1 1.vcf.gz \
    --vcf_2 2.vcf.gz
  """
}
