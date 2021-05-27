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
include { discover_inputs } from './lib/utility.groovy'
include { prepare_snv_channel } from './lib/utility.groovy'

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

  // Filter non-PASS small variants
  // Format (ch_snv_pass): [vcf_type, flags, vcf]
  ch_snv_pass = module_variants_pass(ch_snv.map { it[0..2] })

  // Select input vcfs that have no index and add newly created vcfs for indexing
  // Format (ch_vcfs_no_index): [vcf_type, flags, vcf]
  ch_snv_no_index = ch_snv
    .filter { ! (it[1] & FlagBits.INDEXED) }
    .map { it[0..2] }
    .mix(ch_snv_pass)

  // Index vcfs and join with vcfs that already have an index
  // Format (ch_vcfs_indexed_all): [vcf_type, flags, vcf, vcf_index]
  ch_snv_indexed = module_index_vcf(ch_snv_no_index)
  ch_snv_indexed_all = ch_snv_indexed
    .mix(ch_snv.filter { it[1] & FlagBits.INDEXED })

  // Prepare/group/format VCF channel and then observe differences between VCFs
  // Format (ch_snv_prepared): [vcf_type, flags, vcf_one, index_one, vcf_two, index_two]
  ch_snv_prepared = prepare_snv_channel(ch_snv_indexed_all)
  // Format (ch_snv_intersects): [vcf_type, flags, [0000.vcf, 0001.vcf, 0002.vcf]]
  ch_snv_intersects = module_variants_intersect(ch_snv_prepared)

  // Create channels for counting
  // Format (ch_snv_to_count): [vcf_type, flags, vcf]
  ch_snv_to_count = Channel.empty().mix(
     // Update flag position for unpacked VCFs; `flags` variable here always in respect to vcf_one wrt position
    ch_snv_prepared.flatMap { vcf_type, flags, vcf_one, index_one, vcf_two, index_two ->
      flags_one = flags
      flags_two = flags ^ FlagBits.PTWO
      return [[vcf_type, flags_one, vcf_one], [vcf_type, flags_two, vcf_two]]
    },
    // Set distinct name
    ch_snv_intersects.flatMap { d ->
      d[2].collect { dd -> ["${d[0]}__intersect", d[1], dd] }
    }
  )

  // Variant counts
  // Format (ch_snv_counts): [vcf_counts.tsv]
  ch_snv_counts = module_count_variants(ch_snv_to_count)
  module_combine_counts(ch_snv_counts.collect())
}
