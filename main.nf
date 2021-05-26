#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

// Import modules
include { module_combine_counts } from './modules/combine_counts.nf'
include { module_count_variants } from './modules/count_variants.nf'
include { module_index_vcf } from './modules/index_vcf.nf'
include { module_variants_intersect } from './modules/variants_intersect.nf'
include { module_variants_pass } from './modules/variants_pass.nf'
include { module_vcf_copy } from './modules/vcf_copy.nf'

// Import utilities
include { discover_vcfs } from './lib/utility.groovy'
include { prepare_vcf_channel } from './lib/utility.groovy'

// Set inputs
run_dir_one = file('data/1.1.3/CUP-Pairs8/CUP-Pairs8__PRJ180660_8_DNA009529_FFPE/')
run_dir_two = file('data/1.1.0-rc.8-d6558f5734/CUP-Pairs8/CUP-Pairs8__PRJ180660_8_DNA009529_FFPE/')

// Discover vcfs
ch_vcfs = discover_vcfs(run_dir_one, run_dir_two)

workflow {
  // Publish discovered VCFs and indices in output directory
  // Format (in/out): [vcf_type, flags, vcf, vcf_index]
  ch_vcfs_all = module_vcf_copy(ch_vcfs)

  // Filter non-PASS variants
  // Format (in/out): [vcf_type, flags, vcf]
  ch_vcfs_pass = module_variants_pass(ch_vcfs.map { it[0..2] })

  // Select input vcfs that have no index and add newly created vcfs for indexing
  ch_vcfs_no_index = ch_vcfs_all
    .filter { ! (it[1] & FlagBits.INDEXED) }
    .map { it[0..2] }
    .mix(ch_vcfs_pass)

  // Index vcfs and join with vcfs that already have an index
  ch_vcfs_indexed = module_index_vcf(ch_vcfs_no_index)
  ch_vcfs_indexed_all = ch_vcfs_indexed
    .mix(ch_vcfs.filter { it[1] & FlagBits.INDEXED })

  // Prepare/group/format VCF channel and then observe differences between VCFs
  // Format: [vcf_type, flags, vcf_one, index_one, vcf_two, index_two]
  ch_vcfs_prepared = prepare_vcf_channel(ch_vcfs_indexed_all)
  ch_vcfs_intersects = module_variants_intersect(ch_vcfs_prepared)

  // Create channels for counting
  // Format: [vcf_type, flags, vcf]
  ch_vcfs_to_count = Channel.empty().mix(
     // Update flag position for unpacked VCFs; `flags` variable here always in respect to vcf_one wrt position
    ch_vcfs_prepared.flatMap { vcf_type, flags, vcf_one, index_one, vcf_two, index_two ->
      flags_one = flags
      flags_two = flags ^ FlagBits.PTWO
      return [[vcf_type, flags_one, vcf_one], [vcf_type, flags_two, vcf_two]]
    },
    // Set distinct name
    ch_vcfs_intersects.flatMap { d ->
      d[2].collect { dd -> ["${d[0]}__intersect", d[1], dd] }
    }
  )

  // Variant counts
  ch_counts = module_count_variants(ch_vcfs_to_count)
  combine_counts = module_combine_counts(ch_counts.collect())
}
