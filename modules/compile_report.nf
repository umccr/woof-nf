process module_compile_report {
  publishDir "${params.output_dir}/"

  input:
  //TBD

  output:
  path('*.html')

  script:
  """
  touch report.html
  """
}
