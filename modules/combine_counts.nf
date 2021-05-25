process module_combine_counts {
  publishDir "${params.output_dir}/3_variant_counts/"

  container 'public.ecr.aws/amazonlinux/amazonlinux:latest'

  input:
  path(counts)

  output:
  path('*tsv')

  script:
  """
  {
    echo -e 'vcf_type\tfilename\tsource\tcount';
    cat ${counts};
  } > counts.tsv
  """
}
