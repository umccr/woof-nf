import java.nio.file.Paths

// Format: [input_name, [subdirectory_path, regex_selector]]
input_file_locations = [
  'cpsr': ['small_variants', ~/^.+-germline\.predispose_genes\.vcf\.gz$/],
  'pcgr': ['small_variants', ~/^.+-somatic-PASS\.vcf\.gz$/],
  'manta': ['structural', ~/^.+-manta\.vcf\.gz$/],
  'purple': ['purple', ~/^.+\.purple\.cnv\.gene\.tsv$/],
]

def discover_inputs(dir_one, dir_two) {
  // Locate inputs files in each input directory (as defined in `input_file_locations`)
  inputs_one = discover_inputs_in_dir(dir_one)
  inputs_two = discover_inputs_in_dir(dir_two)
  // Collate input files, include only if comparison is possible otherwise warn
  inputs_cnv = []
  inputs_snv = []
  inputs_sv = []
  input_file_locations.keySet().each { k ->
    if (inputs_one[k] == null | inputs_two[k] == null) {
      // Warn
    } else {
      if (k == 'purple') {
        inputs_cnv << [k, 0, inputs_one[k]]
        inputs_cnv << [k, FlagBits.PTWO, inputs_two[k]]
      } else if (k == 'cpsr' | k == 'pcgr') {
        inputs_snv << [k, 0, inputs_one[k]]
        inputs_snv << [k, FlagBits.PTWO, inputs_two[k]]
      } else if (k == 'manta') {
        inputs_sv << [k, 0, inputs_one[k]]
        inputs_sv << [k, FlagBits.PTWO, inputs_two[k]]
      } else {
        assert false
      }
    }
  }
  // Check for existing VCF indices
  inputs_snv_with_index = locate_vcf_indices(inputs_snv)
  inputs_sv_with_index = locate_vcf_indices(inputs_sv)
  // Create and return channel of inputs
  return [
    Channel.fromList(inputs_cnv),
    Channel.fromList(inputs_snv_with_index),
    Channel.fromList(inputs_sv_with_index)
  ]
}

def discover_inputs_in_dir(directory) {
  // Find all input files
  input_filelist = [:]
  input_file_locations.each { name, val ->
    subdirectory = val[0]
    regex = val[1]
    input_filelist[name] = []
    directory_fullpath = directory / subdirectory
    if (directory_fullpath.exists()) {
      (directory / subdirectory).eachFileMatch(groovy.io.FileType.FILES, regex, { input_filelist[name] << it })
    }
  }
  // Unpack list of discovered input file as:
  // input_filelist[my_key] = input_filepath
  input_filelist.keySet().each { k ->
    // Set key value to filepath itself or null if missing, or raise error where more than one file found
    n_files = input_filelist[k].size()
    if (n_files == 1) {
      input_filelist[k] = input_filelist[k][0]
    } else if (n_files == 0) {
      input_filelist[k] = null
    } else if (n_files > 1) {
      filenames = input_filelist[k].join('\n')
      regex = input_file_locations[k][1]
      exit 1, "ERROR: expected zero or one file for $k but got $n_files with '$regex':\n\n$filenames"
    }
  }
  return input_filelist
}

def locate_vcf_indices(inputs) {
  inputs.eachWithIndex { v, i ->
    file = v[2]
    if (file.toString().endsWith('.tsv')) {
      return
    }
    vcf_index = file + '.tbi'
    if (vcf_index.exists()) {
      inputs[i][1] |= FlagBits.INDEXED
      inputs[i] << vcf_index
    } else {
      inputs[i][1] &= ~FlagBits.INDEXED
      // NOTE: using Path instance to avoid NF restrictions on path() process inputs
      inputs[i] << Paths.get('NO_FILE')
    }
  }
  return inputs
}

def prepare_snv_channel(ch_vcfs) {
  // Pair and correctly order VCFs and indices
  // Input and filtered VCFs must be split first to group correctly
  // Format: [vcf_type, flags, vcf_one, index_one, vcf_two, index_two]
  ch_vcfs_split = ch_vcfs
    .branch {
      input: ! (it[1] & FlagBits.FILTERED)
      filtered: it[1] & FlagBits.FILTERED
    }
  ch_vcfs_paired_input = pair_vcf_and_indices(ch_vcfs_split.input)
  ch_vcfs_paired_filtered = pair_vcf_and_indices(ch_vcfs_split.filtered)
  return Channel.empty().mix(ch_vcfs_paired_input, ch_vcfs_paired_filtered)
}

def pair_vcf_and_indices(ch_vcf_and_indices) {
  // Pair and correctly order VCFs and indices
  // Format: [vcf_type, flags, vcf_one, index_one, vcf_two, index_two]
  ch_result = ch_vcf_and_indices
    .groupTuple()
    .map { vcf_type, flags, vcfs, vcf_indices ->
      def index_one = null
      def index_two = null
      if (flags[0] & FlagBits.PTWO) {
        // First element is position two
        index_one = 1
        index_two = 0
      } else if (flags[1] & FlagBits.PTWO) {
        // Second element is position two
        index_one = 0
        index_two = 1
      } else {
        // TODO: assertion
      }
      // Check flags are consistent - position expected to differ
      check_bits = FlagBits.FILTERED ^ FlagBits.INDEXED
      if ((flags[0] & check_bits) != (flags[1] & check_bits)) {
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
