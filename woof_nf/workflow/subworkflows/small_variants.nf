// Modules
include { module_index_vcf } from '../modules/index_vcf.nf'
include { module_smlv_counts_combine } from '../modules/smlv_counts_combine.nf'
include { module_smlv_count } from '../modules/smlv_count.nf'
include { module_smlv_comparison } from '../modules/comparison_smlv.nf'
include { module_smlv_intersect } from '../modules/smlv_intersect.nf'
include { module_smlv_pass } from '../modules/smlv_pass.nf'

// Utility
include { prepare_smlv_channel } from '../lib/utility.groovy'

workflow workflow_small_variants {
  take:
    // Format (input): [attributes, vcf, vcf_index]
    ch_smlv
  main:
    // Filter non-PASS small variants
    // Format (ch_smlv_pass): [attributes, vcf]
    ch_smlv_pass = module_smlv_pass(ch_smlv.map { it[0..1] })

    // Select input VCFs that have no index and add newly created VCFs for indexing
    // Format (ch_vcfs_no_index): [attributes, vcf]
    ch_smlv_no_index = ch_smlv
      .filter { ! it[0].indexed }
      .map { it[0..1] }
      .mix(ch_smlv_pass)

    // Index VCFs and join with those already indexed
    // Format (ch_vcfs_indexed_all): [attributes, vcf, vcf_index]
    ch_smlv_indexed = module_index_vcf(ch_smlv_no_index)
    ch_smlv_indexed_all = ch_smlv_indexed
      .mix(ch_smlv.filter { it[0].indexed })

    // Prepare/group/format VCF channel and then determine differences between VCFs
    // Format (ch_smlv_prepared): [attributes, vcf_one, index_one, vcf_two, index_two]
    ch_smlv_prepared = prepare_smlv_channel(ch_smlv_indexed_all)
    // Format (ch_smlv_intersects): [attributes, [0000.vcf, 0001.vcf, 0002.vcf]]
    ch_smlv_intersects = module_smlv_intersect(ch_smlv_prepared)

    // Make SNV comparison
    // Format (module_smlv_comparison: input): [attributes, vcf_0, vcf_1, vcf_2]
    ch_smlv_comparison = module_smlv_comparison(
        ch_smlv_intersects.map { it.flatten() }
    )

    // Create channels for counting
    // Format (ch_smlv_to_count): [attributes, vcf]
    ch_smlv_to_count = Channel.empty().mix(
       // Update run_number for unpacked VCFs
      ch_smlv_prepared.flatMap { attributes, vcf_one, index_one, vcf_two, index_two ->
        attrs_one = attributes.clone()
        attrs_two = attributes.clone()
        attrs_one.run_number = 'one'
        attrs_two.run_number = 'two'
        return [[attrs_one, vcf_one], [attrs_two, vcf_two]]
      },
      // Set distinct name
      // Format (out): [attributes, vcf]; Attributes.data_source is modified
      ch_smlv_intersects.flatMap { d ->
        // Format (d): [attributes, [0000.vcf, 0001.vcf, 0002.vcf]]
        // Format (dd): [0000.vcf, 0001.vcf, 0002.vcf]
        d[1].collect { dd ->
          attributes = d[0].clone()
          attributes.data_source = "${attributes.data_source}__intersect"
          [attributes, dd]
        }
      }
    )

    // Variant counts
    // Format (ch_smlv_counts): [attributes, vcf_counts]
    ch_smlv_counts = module_smlv_count(ch_smlv_to_count)
    ch_smlv_counts_grouped = ch_smlv_counts
      // As we cannot directly call groupTuple on Attributes, we construct the group key and place at index 0:
      // Format: [sample_name, file]
      .map { attrs, file -> tuple( groupKey([attrs.sample_name, attrs.run_type], 0), file ) }
      // Now we can collect with groupTuple
      // Format: [sample_name, run_type, [files]]
      .groupTuple()
      .map { group_key, files -> [group_key[0], group_key[1], files] }
    ch_smlv_counts_combined = module_smlv_counts_combine(ch_smlv_counts_grouped)
  emit:
    ch_smlv_counts_combined.counts
    ch_smlv_comparison.comparison
}
