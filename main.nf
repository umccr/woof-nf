#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

include { module_variants_pass } from './modules/variants_pass.nf'
include { workflow_compare_vcfs } from './workflows/vcf_comparison.nf'

// Inputs
ch_vcf_one = file('data/prev/1/gs_one.vcf.gz')
ch_vcf_two = file('data/prev/1/gs_two.vcf.gz')
//ch_vcf_one = file('/Users/stephen/projects/pipeline_comparison/data/1.1.3/CUP-Pairs8/CUP-Pairs8__PRJ180660_8_DNA009529_FFPE/small_variants/CUP-Pairs8__PRJ180660_8_DNA009529_FFPE-somatic.vcf.gz')
//ch_vcf_two = file('/Users/stephen/projects/pipeline_comparison/data/1.0.9-bfab109526/CUP-Pairs8/CUP-Pairs8__PRJ180660_8_DNA009529_FFPE/small_variants/CUP-Pairs8__PRJ180660_8_DNA009529_FFPE-somatic.vcf.gz')
ch_vcfs_input = Channel.fromList([
  ['one', ch_vcf_one],
  ['two', ch_vcf_two],
])

workflow {
  // Filter variants
  ch_vcfs_pass = module_variants_pass(ch_vcfs_input)

  // Tag inputs to track and re-pair downstream
  ch_vcfs = Channel.empty().mix(
    Channel.value('pass').combine(ch_vcfs_pass),
    Channel.value('input').combine(ch_vcfs_input)
  )

  // Perform comparison
  workflow_compare_vcfs(ch_vcfs)
}
