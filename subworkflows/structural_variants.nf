// Import modules
include { module_sv_comparison } from '../modules/sv_comparison.nf'

// Import utility
include { pair_files } from '../lib/utility.groovy'

workflow workflow_structural_variants {
  take:
    ch_sv
  main:
    ch_sv_prepared = pair_files(ch_sv)
    module_sv_comparison(ch_sv_prepared)
}
