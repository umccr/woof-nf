process module_create_report {
  publishDir "${params.output_dir}"

  input:
  path(comparison_dir)
  val(workflow_files)

  output:
  path('report.html')

  script:
  """
  create_report.py \
    --input_dir "${comparison_dir}" \
    --output_fp report.html
  """
}

