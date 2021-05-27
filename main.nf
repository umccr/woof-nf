#!/usr/bin/env nextflow
// Silently enable DSL2
nextflow.enable.dsl = 2

// Import modules, subworkflows, and utility
include { module_vcf_copy } from './modules/vcf_copy.nf'
include { workflow_small_variants } from './subworkflows/small_variants.nf'
include { discover_inputs } from './lib/utility.groovy'

// Set inputs
run_dir_one = file('data/1.0.3-rc.11/CUP-Pairs8/')
run_dir_two = file('data/1.2.0/CUP-Pairs8/')

// Discover inputs
(ch_cnv, ch_snv, ch_sv) = discover_inputs(run_dir_one, run_dir_two)

workflow {
  // TODO: check if we still want to publish input files, maybe not
  // Publish discovered VCFs and indices in output directory
  // Format (ch_vcfs, ch_vcfs_all): [vcf_type, flags, vcf, vcf_index]
  //ch_vcfs_all = module_vcf_copy(ch_vcfs)

  workflow_small_variants(ch_snv)
}
