#!/usr/bin/env nextflow
// Silently enable DSL2
nextflow.enable.dsl = 2

// Import modules, workflows
include { module_compile_report } from './modules/compile_report.nf'
include { workflow_copy_number_variants } from './subworkflows/copy_number_variants.nf'
include { workflow_small_variants } from './subworkflows/small_variants.nf'
include { workflow_structural_variants } from './subworkflows/structural_variants.nf'

// Import utility
include { process_inputs } from './lib/utility.groovy'

// Read input files from disk
// TODO: expose to config and cli
if (! params.inputs_fp) {
    exit 1, "error: got bad inputs_fp argument"
}
inputs_fp = file(params.inputs_fp)
input_files = inputs_fp
  .readLines()[1..-1]
  .collect { it.split('\t') }

// Discover inputs
(ch_cnv, ch_smlv, ch_sv) = process_inputs(input_files)

workflow {
  // Run comparisons
  workflow_copy_number_variants(ch_cnv)
  workflow_small_variants(ch_smlv)
  workflow_structural_variants(ch_sv)

  // Compile report
  //module_compile_report()
}
