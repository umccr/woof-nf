#!/usr/bin/env nextflow
// Silently enable DSL2
nextflow.enable.dsl = 2

// Import workflows
include { workflow_copy_number_variants } from './subworkflows/copy_number_variants.nf'
include { workflow_small_variants } from './subworkflows/small_variants.nf'
include { workflow_structural_variants } from './subworkflows/structural_variants.nf'

// Import utility
include { discover_inputs } from './lib/utility.groovy'

// Set inputs
run_dir_one = file('data/1.0.3-rc.11/CUP-Pairs8/')
run_dir_two = file('data/1.2.0/CUP-Pairs8/')

// Discover inputs
(ch_cnv, ch_snv, ch_sv) = discover_inputs(run_dir_one, run_dir_two)

workflow {
  workflow_copy_number_variants(ch_cnv)
  workflow_small_variants(ch_snv)
  workflow_structural_variants(ch_sv)
}
