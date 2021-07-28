// Import modules
include { module_cnv_comparison } from '../modules/comparison_cnv.nf'

// Import utility
include { pair_files } from '../lib/utility.groovy'

workflow workflow_copy_number_variants {
  take:
    ch_cnv
  main:
    ch_cnv_prepared = pair_files(ch_cnv)
    ch_cnv_comparison = module_cnv_comparison(ch_cnv_prepared)
  emit:
    ch_cnv_comparison.cn_diff
    ch_cnv_comparison.cn_diff_coord
}
