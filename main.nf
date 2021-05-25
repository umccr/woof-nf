#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

// Import modules
include { module_combine_counts } from './modules/combine_counts.nf'
include { module_count_variants } from './modules/count_variants.nf'
include { module_index_vcf } from './modules/index_vcf.nf'
include { module_variants_intersect } from './modules/variants_intersect.nf'
include { module_variants_pass } from './modules/variants_pass.nf'

// Import utilities
include { pair_vcfs_and_indices } from './lib/utility.groovy'

// Set inputs
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

def prepare_vcf_channel(ch_vcfs) {
  ch_vcfs_split = ch_vcfs
    .branch {
      input: ! (it[1] & 0b0001)
      filtered: it[1] & 0b0001
    }
  ch_vcfs_paired_input = pair_vcf_and_indices(ch_vcfs_split.input)
  ch_vcfs_paired_filtered = pair_vcf_and_indices(ch_vcfs_split.filtered)
  return Channel.empty().mix(ch_vcfs_paired_input, ch_vcfs_paired_filtered)
}

def pair_vcf_and_indices(ch_vcf_and_indices) {
  ch_result = ch_vcf_and_indices
    .groupTuple()
    .map { vcf_type, flags, vcfs, vcf_indices ->
      if (flags[0] & 0b0010) {
        // First element is position two
        index_one = 1
        index_two = 0
      } else if (flags[1] & 0b0010) {
        // Second element is position two
        index_one = 0
        index_two = 1
      } else {
        // TODO: assertion
      }


      //// Set single flag for source type
      //if ((flags[0] & 0b0001) != (flags[1] & 0b0001)) {
      //  // TODO: assertion
      //} else if (flags[0] & 0b0001) {
      //  source = 'input'
      //} else {
      //  source = 'filtered'
      //}

      // Check flags are consistent - position expected to differ
      if ((flags[0] & 0b0101) != (flags[1] & 0b0101)) {
        // TODO: assertion
      }

      return [
        vcf_type,
        flags[index_one],
        vcfs[index_one],
        vcf_indices[index_one],
        vcfs[index_two],
        vcf_indices[index_two]
      ]
    }
  return ch_result
}

workflow {
  // Filter variants
  // Select only [vcf_type, flags, vcf_filepath]
  ch_vcfs_pass = module_variants_pass(ch_vcfs.map { it[0..2] })

  // Select input vcfs that have no index and add newly created vcfs for indexing
  ch_vcfs_no_index = ch_vcfs
    .filter { ! (it[1] & 0b0100) }
    .map { it[0..2] }
    .mix(ch_vcfs_pass)

  // Index vcfs and join with vcfs that already have an index
  ch_vcfs_indexed = module_index_vcf(ch_vcfs_no_index)
  ch_vcfs_indexed_all = ch_vcfs_indexed
    .mix(ch_vcfs.filter { it[1] & 0b0100 })

  ch_vcfs_prepared = prepare_vcf_channel(ch_vcfs_indexed_all)

  ch_vcfs_intersects = module_variants_intersect(ch_vcfs_prepared)

  // Variant counts
  ch_vcfs_to_count = Channel.empty().mix(
    ch_vcfs_prepared.flatMap { vcf_type, flags, vcf_one, index_one, vcf_two, index_two ->
      flags_one = flags
      flags_two = flags ^ 0b0001
      return [[vcf_type, flags_one, vcf_one], [vcf_type, flags_two, vcf_two]]
    },
    ch_vcfs_intersects.flatMap { d ->
      d[2].collect { dd -> ["${d[0]}__intersect", d[1], dd] }
    }
  )
  ch_counts = module_count_variants(ch_vcfs_to_count)
  combine_counts = module_combine_counts(ch_counts.collect())
}
