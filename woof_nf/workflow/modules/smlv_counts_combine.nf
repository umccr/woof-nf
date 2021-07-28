process module_smlv_counts_combine {
  publishDir "${publish_dir}"

  input:
  tuple val(sample_name), val(run_type), path(counts)

  output:
  path('*tsv'), emit: counts

  script:
  publish_basedir = "${params.output_dir}/${sample_name}"
  publish_dir = "${publish_basedir}/${run_type}/small_variants/"
  """
  {
    echo -e 'vcf_type\tfilename\trun\tsource\tcount';
    cat ${counts};
  } > counts.tsv
  """
}
