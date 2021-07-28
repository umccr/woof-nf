// Import modules
include { module_sv_comparison } from '../modules/comparison_sv.nf'

// Import utility
include { pair_files } from '../lib/utility.groovy'

workflow workflow_structural_variants {
  take:
    ch_sv
  main:
    ch_sv_prepared = pair_files(ch_sv)
    ch_sv_comparison = module_sv_comparison(ch_sv_prepared)
  emit:
    ch_sv_comparison.circos
    ch_sv_comparison.metrics
    ch_sv_comparison.fpfn
}
