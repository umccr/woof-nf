include { module_count_variants } from '../modules/count_variants.nf'
include { module_index_vcf } from '../modules/index_vcf.nf'
include { module_variants_intersect } from '../modules/variants_intersect.nf'

include { pair_vcfs_and_indices } from '../lib/utility.groovy'


workflow workflow_compare_vcfs {
  take: ch_vcfs
  main:
  // Index
  ch_vcfs_indices = module_index_vcf(ch_vcfs)

  // Pair and sort VCFs and corresponding indices
  ch_vcfs_indexed = pair_vcfs_and_indices(ch_vcfs, ch_vcfs_indices)

  // Intersect
  ch_vcfs_intersects = module_variants_intersect(ch_vcfs_indexed)

  // Variant counts
  ch_vcfs_to_count = Channel.empty().mix(
    ch_vcfs.map { [it[0], it[2]] },
    ch_vcfs_intersects.flatMap { d ->
      d[2].collect { dd -> ["${d[0]}_intersect", dd] }
    }
  )
  module_count_variants(ch_vcfs_to_count)
}
