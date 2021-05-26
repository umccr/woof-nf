process module_vcf_copy {
  publishDir "${params.output_dir}/1_vcfs/"

  executor 'local'

  input:
  tuple val(vcf_type), val(flags), path(vcf), path(vcf_index)

  output:
  tuple val(vcf_type), val(flags), path('*.vcf.gz'), path('*.vcf.gz.tbi')

  script:
  run = (flags & FlagBits.PTWO) ? 'second' : 'first'
  sample_name = "${run}__${vcf_type}__all__${vcf.getSimpleName()}"
  """
  ln -s "${vcf}" "${sample_name}.vcf.gz"
  if [[ "${vcf_index}" == "NO_FILE" ]]; then
    # NOTE: this is required to provide expected output for the NF process
    # Ideally an output path could match one of two globs; i.e. the created
    # index or the input NO_FILE placeholder file.
    touch NO_FILE.vcf.gz.tbi
  else
    ln -s "${vcf_index}" "${sample_name}.vcf.gz.tbi"
  fi;
  """
}
