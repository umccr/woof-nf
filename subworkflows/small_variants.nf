// Modules
include { module_combine_counts } from '../modules/combine_counts.nf'
include { module_count_variants } from '../modules/count_variants.nf'
include { module_index_vcf } from '../modules/index_vcf.nf'
include { module_snv_comparison } from '../modules/snv_comparison.nf'
include { module_variants_intersect } from '../modules/variants_intersect.nf'
include { module_variants_pass } from '../modules/variants_pass.nf'

// Utility
include { prepare_snv_channel } from '../lib/utility.groovy'

workflow workflow_small_variants {
  take:
    ch_snv
  main:
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

    // Make SNV comparison
    module_snv_comparison(ch_snv_intersects.map { it.flatten() })

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
