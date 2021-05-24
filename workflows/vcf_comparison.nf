include { module_count_variants } from '../modules/count_variants.nf'
include { module_variants_intersect } from '../modules/variants_intersect.nf'

workflow workflow_compare_vcfs {
  take: ch_vcfs
  main:
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
