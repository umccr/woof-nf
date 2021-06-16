process module_sv_comparison {
  publishDir "${params.output_dir}/${sample_name}/structural_variants/"

  input:
  tuple val(sample_name), path('1.vcf.gz'), path('2.vcf.gz')

  output:
  path('circos/*')
  path('eval_metrics.tsv')
  path('fpfn.tsv')

  script:
  """
  comparison_sv.py \
    --sample_name "${sample_name}" \
    --file_source "${sample_name}_TEMP_FILESOURCE" \
    --vcf_1 1.vcf.gz \
    --vcf_2 2.vcf.gz
  """
}
