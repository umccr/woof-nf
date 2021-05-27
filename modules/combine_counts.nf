process module_combine_counts {
  publishDir "${params.output_dir}/small_variants/"

  container 'public.ecr.aws/amazonlinux/amazonlinux:latest'

  input:
  path(counts)

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
