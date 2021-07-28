#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

// Import workflows and modules
include { workflow_copy_number_variants } from './subworkflows/copy_number_variants.nf'
include { workflow_small_variants } from './subworkflows/small_variants.nf'
include { workflow_structural_variants } from './subworkflows/structural_variants.nf'
include { module_create_report } from './modules/create_report.nf'

// Import utility
include { process_inputs } from './lib/utility.groovy'

// Check configuration
if (! params.inputs_fp) {
    exit 1, "error: got bad inputs_fp argument"
}
if (! params.output_dir) {
    exit 1, "error: got bad output_dir argument"
}

// Read input files from disk
inputs_fp = file(params.inputs_fp)
input_files = inputs_fp
  .readLines()[1..-1]
  .collect { it.split('\t') }

// Collect inputs into appropriate channels
(ch_cnv, ch_smlv, ch_sv) = process_inputs(input_files)

workflow {
  wf_cnv = workflow_copy_number_variants(ch_cnv)
  wf_smlv = workflow_small_variants(ch_smlv)
  wf_sv = workflow_structural_variants(ch_sv)

  ch_comparison_dir = Channel.fromPath(params.output_dir)
  wf_files = Channel.empty().mix(wf_cnv, wf_smlv, wf_sv).collect()
  module_create_report(ch_comparison_dir, wf_files)
}
