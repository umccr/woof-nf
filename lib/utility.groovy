import java.nio.file.Paths

def process_inputs(input_files) {
  // Collate input files, include only if comparison is possible otherwise warn
  inputs_cnv = []
  inputs_smlv = []
  inputs_sv = []
  input_files.each { d ->
    // Unpack and cast here; error raises while trying to unpack in closure params
    (sample_name, variant_type, file_source, run_number, filepath) = d
    filepath = file(filepath)
    // Get flags (position/run one or two)
    if (run_number == 'first') {
      flags = 0
    } else if (run_number == 'second') {
      flags = FlagBits.PTWO
    } else {
     assert false
    }
    // Sort into appropriate list
    if (variant_type  == 'copy_number_variants') {
      inputs_cnv << [sample_name, file_source, flags, filepath]
    } else if (variant_type == 'small_variants') {
      inputs_smlv << [sample_name, file_source, flags, filepath]
    } else if (variant_type == 'structural_variants') {
      inputs_sv << [sample_name, file_source, flags, filepath]
    } else {
      assert false
    }
  }
  // Check for existing VCF indices
  inputs_smlv_with_index = locate_vcf_indices(inputs_smlv)
  // Create and return channel of inputs
  return [
    Channel.fromList(inputs_cnv),
    Channel.fromList(inputs_smlv_with_index),
    Channel.fromList(inputs_sv)
  ]
}


def locate_vcf_indices(inputs) {
  inputs.eachWithIndex { v, i ->
    file = v[3]
    if (file.toString().endsWith('.tsv')) {
      return
    }
    vcf_index = file + '.tbi'
    if (vcf_index.exists()) {
      inputs[i][2] |= FlagBits.INDEXED
      inputs[i] << vcf_index
    } else {
      inputs[i][2] &= ~FlagBits.INDEXED
      // NOTE: using Path instance to avoid NF restrictions on path() process inputs
      inputs[i] << Paths.get('NO_FILE')
    }
  }
  return inputs
}

def prepare_smlv_channel(ch_vcfs) {
  // Pair and correctly order VCFs and indices
  // Input and filtered VCFs must be split first to group correctly
  // Format: [sample_name, vcf_type, flags, vcf_one, index_one, vcf_two, index_two]
  ch_vcfs_split = ch_vcfs
    .branch {
      input: ! (it[2] & FlagBits.FILTERED)
      filtered: it[2] & FlagBits.FILTERED
    }
  ch_vcfs_paired_input = pair_vcf_and_indices(ch_vcfs_split.input)
  ch_vcfs_paired_filtered = pair_vcf_and_indices(ch_vcfs_split.filtered)
  return Channel.empty().mix(ch_vcfs_paired_input, ch_vcfs_paired_filtered)
}

def pair_vcf_and_indices(ch_vcf_and_indices) {
  // Pair and correctly order VCFs and indices
  // Format: [sample_name, vcf_type, flags, vcf_one, index_one, vcf_two, index_two]
  ch_result = ch_vcf_and_indices
    .groupTuple(by: [0, 1])
    .map { sample_name, vcf_type, flags, vcfs, vcf_indices ->
      // Get index of first and second file
      (index_one, index_two) = get_file_order(flags)
      // Check flags are consistent
      check_flag_consistency(flags)
      return [
        sample_name,
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

def pair_files(ch_files) {
  ch_result = ch_files
    .groupTuple()
    .map { sample_name, input_types, flags, files ->
      // Get index of first and second file
      (index_one, index_two) = get_file_order(flags)
      // Check data is consistent
      check_flag_consistency(flags)
      assert input_types.unique().size() == 1
      return [
        sample_name,
        files[index_one],
        files[index_two],
      ]
    }
  return ch_result
}

def get_file_order(flags) {
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
  return [index_one, index_two]
}

def check_flag_consistency(flags) {
  // Check flags are consistent - position expected to differ
  check_bits = FlagBits.FILTERED ^ FlagBits.INDEXED
  if ((flags[0] & check_bits) != (flags[1] & check_bits)) {
    // TODO: assertion
  }
}
