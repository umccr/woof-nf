process module_smlv_counts_combine {
  publishDir "${params.output_dir}/${sample_name}/small_variants/"

  container 'public.ecr.aws/amazonlinux/amazonlinux:latest'

  input:
  tuple val(sample_name), path(counts)

  output:
  path('*tsv')

  script:
  """
  {
    echo -e 'vcf_type\tfilename\trun\tsource\tcount';
    cat ${counts};
  } > counts.tsv
  """
}
