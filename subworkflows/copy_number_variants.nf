// Import modules
include { module_cnv_comparison } from '../modules/cnv_comparison.nf'

// Import utility
include { pair_files } from '../lib/utility.groovy'

workflow workflow_copy_number_variants {
  take:
    ch_cnv
  main:
    ch_cnv_prepared = pair_files(ch_cnv)
    module_cnv_comparison(ch_cnv_prepared)
}
