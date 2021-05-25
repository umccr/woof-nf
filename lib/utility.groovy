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

def discover_vcfs(dir_one, dir_two) {
  vcfs_one = discover_vcfs_in_dir(dir_one)
  vcfs_two = discover_vcfs_in_dir(dir_two)
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
  // Create and return channel of input vcfs
  return Channel.fromList(vcfs)
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

def discover_vcfs_in_dir(directory) {
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

def pair_vcfs_and_indices(ch_vcfs, ch_vcfs_indices) {
  ch_vcfs_indexed = ch_vcfs
    .join(ch_vcfs_indices, by: [0, 1])
    .toList()
    .flatMap { d ->
      // Output channel to contain:
      //   ['input', vcf_input_one, index_input_one, vcf_input_two, index_input_two]
      //   ['pass', vcf_pass_one, index_pass_one, vcf_pass_two, index_pass_two]
      input = []
      pass = []
      d.collect { dd ->
        // Determine position in input/pass array: vcf_one is first, vcf_two is second
        if (dd[1] == 'one') {
          position = 0
        } else if (dd[1] == 'two') {
          position = 1
        } else {
          // TODO: assertion
        }
        // Insert into correct array at the appropriate position
        if (dd[0]=='input') {
          input[position] = dd[2..-1]
        } else if (dd[0]=='pass') {
          pass[position] = dd[2..-1]
        } else {
          // TODO: assertion
        }
      }
      return [
        ['input', *input.flatten()],
        ['pass', *pass.flatten()]
      ]
    }
  return ch_vcfs_indexed
}
