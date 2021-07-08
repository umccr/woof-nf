process module_smlv_counts_combine {
  publishDir "${params.output_dir}/${attributes_in.sample_name}/small_variants/"

  input:
  tuple val(attributes_in), path(counts)

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
