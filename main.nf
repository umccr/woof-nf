#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

include { module_variants_pass } from './modules/variants_pass.nf'
include { workflow_compare_vcfs } from './workflows/vcf_comparison.nf'

// Inputs
run_dir_one = file('data/1.1.3/CUP-Pairs8/CUP-Pairs8__PRJ180660_8_DNA009529_FFPE/')
run_dir_two = file('data/1.1.0-rc.8-d6558f5734/CUP-Pairs8/CUP-Pairs8__PRJ180660_8_DNA009529_FFPE/')

// Format: [vcf_name, [subdirectory_path, regex_selector]]
vcf_locations = [
  'purple_somatic': ['purple', ~/^.+purple\.somatic\.vcf\.gz$/],
  'purple_sv': ['purple', ~/^.+purple\.sv\.vcf\.gz$/],
  'manta': ['structural', ~/^.+manta\.vcf\.gz$/],
  'pierian': ['pierian', ~/^.+manta\.single\.vcf\.gz$/],
  'pierian_somatic': ['pierian', ~/^.+somatic-PASS-single.*\.vcf\.gz$/],
  'small_variants_germline': ['small_variants', ~/^.+germline\.predispose_genes\.vcf\.gz$/],
  'small_variants_somatic': ['small_variants', ~/^.+somatic\.vcf\.gz$/],
  'small_variants_pass': ['small_variants', ~/^.+somatic-PASS\.vcf\.gz$/],
  'small_variants_sage': ['small_variants/sage1/', ~/^.+sage\.vcf\.gz$/],
]

def discover_vcfs(directory) {
  vcf_filelist = [:]
  vcf_locations.each { name, val ->
    subdirectory = val[0]
    regex = val[1]
    vcf_filelist[name] = []
    directory_fullpath = directory / subdirectory
    if (directory_fullpath.exists()) {
      (directory / subdirectory).eachFileMatch(groovy.io.FileType.FILES, regex, { vcf_filelist[name] << it })
    }
  }
  vcf_filelist.keySet().each { k ->
    // Set key value to filepath itself or null if missing, or raise error where more than one file found
    n_files = vcf_filelist[k].size()
    if (n_files == 1) {
      vcf_filelist[k] = vcf_filelist[k][0]
    } else if (n_files == 0) {
      vcf_filelist[k] = null
    } else if (n_files > 1) {
      filenames = vcf_filelist[k].join('\n')
      regex = vcf_locations[k][1]
      exit 1, "ERROR: expected zero or one file for $k but got $n_files with '$regex':\n\n$filenames"
    }
  }
  return vcf_filelist
}

// Discover vcfs
vcfs_one = discover_vcfs(run_dir_one)
vcfs_two = discover_vcfs(run_dir_two)

// Collate vcfs, include only if comparison is possible otherwise warn
vcfs = []
vcf_locations.keySet().each { k ->
  if (vcfs_one[k] == null | vcfs_two[k] == null) {
    // Warn
  } else {
    vcfs << [k, 0b000, vcfs_one[k]]
    vcfs << [k, 0b010, vcfs_two[k]]
  }
}

// Check for existing vcf indices
vcfs.eachWithIndex { v, i ->
  vcf = v[2]
  vcf_index = vcf + '.tbi'


  // NOTE: artificially introducing some unindexed input vcfs
  // REMOVE (DEV)
  if (i % 2 == 0 | i > 2) {
    vcfs[i][1] & ~0b0100
    vcfs[i] << null
    return
  }


  if (vcf_index.exists()) {
    vcfs[i][1] |= 0b0100
    vcfs[i] << vcf_index
  } else {
    vcfs[i][1] &= ~0b0100
    vcfs[i] << null
  }
}

// Create channel of input vcfs
ch_vcfs = Channel.fromList(vcfs)

// TODO: see where this best fits
include { module_index_vcf } from './modules/index_vcf.nf'
include { pair_vcfs_and_indices } from './lib/utility.groovy'

workflow {
  // 4. target channel format:
  //    [vcf_name(small/struct/etc), vcf_1, index_1, vcf_2, index_2]

  // Filter variants
  // Select only [vcf_type, flags, vcf_filepath]
  ch_vcfs_pass = module_variants_pass(ch_vcfs.map { it[0..2] })

  // Select input vcfs that have no index and add newly created vcfs for indexing
  ch_vcfs_no_index = ch_vcfs
    .filter { ! (it[1] & 0b0100) }
    .map { it[0..2] }
    .mix(ch_vcfs_pass)

  // Index vcfs and join with vcfs that already ahve an index
  ch_vcfs_indexed = module_index_vcf(ch_vcfs_no_index)
  ch_vcfs_indices = ch_vcfs_indexed
    .mix(ch_vcfs.filter { it[1] & 0b0100 })

  // TODO: complete channel transform to target (see above), then complete workflow
  ch_temp = ch_vcfs_indices
    .branch {
      input: ! (it[1] & 0b0001)
      filtered: it[1] & 0b0001
    }

  // Tag inputs to track and re-pair downstream
  //ch_vcfs = Channel.empty().mix(
  //  Channel.value('pass').combine(ch_vcfs_pass),
  //  Channel.value('input').combine(ch_vcfs_input)
  //)

  // Perform comparison
  //workflow_compare_vcfs(ch_vcfs)
}
