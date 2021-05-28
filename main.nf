#!/usr/bin/env nextflow
// Silently enable DSL2
nextflow.enable.dsl = 2

// Import modules, workflows
include { module_compile_report } from './modules/compile_report.nf'
include { workflow_copy_number_variants } from './subworkflows/copy_number_variants.nf'
include { workflow_small_variants } from './subworkflows/small_variants.nf'
include { workflow_structural_variants } from './subworkflows/structural_variants.nf'

// Import utility
include { discover_inputs } from './lib/utility.groovy'

// Set inputs
run_dir_one = file('data/1.0.3-rc.3/COLO829/WGS/2020-01-18/umccrised/COLO829_1__Colo829')
run_dir_two = file('data/1.0.4/COLO829/WGS/2020-01-18/umccrised/COLO829_1__Colo829')

// Discover inputs
(ch_cnv, ch_smlv, ch_sv) = discover_inputs(run_dir_one, run_dir_two)

workflow {
  // TODO: allow multiple samples as input
  // This can be achieved in different ways - not yet entirely clear which is best
  // I think understanding of this will required examining real-work output of umccrise, which
  // may properly come about running umccrise myself. For now, we can implement best-guest
  // placeholder logic:
  //    * two variables: string glob or array thereof; one for each 'run'
  //    * optional sample alias, otherwise infer sample from directory/file names
  //    * require matching of (1) run alias or (2) inferred sample name (allow fallback)
  //    * then perform discovery as done above
  // One other thought: given the Groovy/Java has some disadvantages relative to python in
  // this context, it could be benefical to offload discovery/input processing logic into a
  // python script, which could wrap this pipeline. Though for that to work nicely, I would
  // want to faithfully stream nextflow stdout to console via subprocess - not sure this
  // is possible; investigate

  // Run comparisons
  workflow_copy_number_variants(ch_cnv)
  workflow_small_variants(ch_smlv)
  workflow_structural_variants(ch_sv)

  // Compile report
  //module_compile_report()
}
