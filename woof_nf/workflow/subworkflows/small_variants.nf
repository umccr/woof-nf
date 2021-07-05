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
    ch_smlv
  main:
    // Filter non-PASS small variants
    // Format (ch_smlv_pass): [sample_name, vcf_type, flags, vcf]
    ch_smlv_pass = module_smlv_pass(ch_smlv.map { it[0..3] })

    // Select input VCFs that have no index and add newly created VCFs for indexing
    // Format (ch_vcfs_no_index): [sample_name, vcf_type, flags, vcf]
    ch_smlv_no_index = ch_smlv
      .filter { ! (it[2] & FlagBits.INDEXED) }
      .map { it[0..3] }
      .mix(ch_smlv_pass)

    // Index VCFs and join with those already indexed
    // Format (ch_vcfs_indexed_all): [sample_name, vcf_type, flags, vcf, vcf_index]
    ch_smlv_indexed = module_index_vcf(ch_smlv_no_index)
    ch_smlv_indexed_all = ch_smlv_indexed
      .mix(ch_smlv.filter { it[2] & FlagBits.INDEXED })

    // Prepare/group/format VCF channel and then determine differences between VCFs
    // Format (ch_smlv_prepared): [sample_name, vcf_type, flags, vcf_one, index_one, vcf_two, index_two]
    ch_smlv_prepared = prepare_smlv_channel(ch_smlv_indexed_all)
    // Format (ch_smlv_intersects): [sample_name, vcf_type, flags, [0000.vcf, 0001.vcf, 0002.vcf]]
    ch_smlv_intersects = module_smlv_intersect(ch_smlv_prepared)

    // Make SNV comparison
    // Format: [sample_name, vcf_type, flags, vcf_1, vcf_2, vcf_3]
    module_smlv_comparison(
        ch_smlv_intersects.map { it.flatten() }
    )

    // Create channels for counting
    // Format (ch_smlv_to_count): [sample_name, vcf_type, flags, vcf]
    ch_smlv_to_count = Channel.empty().mix(
       // Update flag position for unpacked VCFs; `flags` variable here always in respect to vcf_one wrt position
      ch_smlv_prepared.flatMap { sample_name, vcf_type, flags, vcf_one, index_one, vcf_two, index_two ->
        flags_one = flags
        flags_two = flags ^ FlagBits.PTWO
        return [[sample_name, vcf_type, flags_one, vcf_one], [sample_name, vcf_type, flags_two, vcf_two]]
      },
      // Set distinct name
      ch_smlv_intersects.flatMap { d ->
        d[3].collect { dd -> [d[0], "${d[1]}__intersect", d[2], dd] }
      }
    )

    // Variant counts
    // Format (ch_smlv_counts): [sample_name, vcf_counts]
    ch_smlv_counts = module_smlv_count(ch_smlv_to_count)
    module_smlv_counts_combine(ch_smlv_counts.groupTuple())
}
