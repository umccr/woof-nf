import java.nio.file.Paths


// I wanted use the class type for Attributes but nextflow includes memory address of the instance when determining the cache
// hash, causing caches to practically always become invalidated when re-running. Nextflow uses the hashCode function to
// obtain a hash of an object:
//
// https://github.com/nextflow-io/nextflow/blob/STABLE-21.04.x/modules/nf-commons/src/main/nextflow/util/CacheHelper.java#L209
//
// This could be dealt with if I was able to override the hashCode function but Nextflow prevents this at compile-time. And
// so, we are instead using a hash. Using a function for more explicit definition.
def create_attributes(
   String sample_name,
   String run_type,
   String run_number,
   String data_source,
   String data_type,
   Boolean filtered,
   Boolean indexed
) {
  [
    sample_name: sample_name,
    run_type: run_type,
    run_number: run_number,
    run_type: run_type,
    data_source: data_source,
    data_type: data_type,
    filtered: filtered,
    indexed: indexed
  ]
}


def process_inputs(input_files) {
  // Collate input files
  def inputs_cnv = []
  def inputs_smlv = []
  def inputs_sv = []
  input_files.each { d ->
    // Unpack and cast here; error raises while trying to unpack in closure params
    (sample_name, run_type, run_number, data_source, data_type, filepath) = d
    def filepath = file(filepath)
    // Restrict some values
    assert run_number in ['one', 'two']
    assert data_type in ['copy_number_variants', 'small_variants', 'structural_variants']
    assert data_source in [
      'cpsr',
      'pcgr',
      'manta',
      'purple',
      'tumour-ensemble',
      'normal-ensemble',
      'normal-gatk',
      'normal-strelka2',
      'normal-vardict'
    ]
    // Set attributes
    def attributes = create_attributes(
     sample_name,
     run_type,
     run_number,
     data_source,
     data_type,
     false,  // filtered
     null  // indexed
    )
    // Sort into appropriate list
    if (attributes.data_type == 'copy_number_variants') {
      inputs_cnv << [attributes, filepath]
    } else if (attributes.data_type == 'small_variants') {
      inputs_smlv << [attributes, filepath]
    } else if (attributes.data_type == 'structural_variants') {
      inputs_sv << [attributes, filepath]
    }
  }
  // Check for existing VCF indices
  def inputs_smlv_with_index = locate_vcf_indices(inputs_smlv)
  // Create and return channel of inputs
  return [
    Channel.fromList(inputs_cnv),
    Channel.fromList(inputs_smlv_with_index),
    Channel.fromList(inputs_sv)
  ]
}


def locate_vcf_indices(inputs) {
  inputs.eachWithIndex { v, i ->
    def file = v[1]
    if (file.toString().endsWith('.tsv')) {
      return
    }
    // NOTE (20210729): calling exists() on an S3Path results in an access denied response from the
    // AWS api, so we avoid doing so here and opt to re-create VCF indices even if they exist on S3
    def vcf_index = file + '.tbi'
    if (vcf_index.getClass() == java.nio.file.Path && vcf_index.exists()) {
      inputs[i][0].indexed = true
      inputs[i] << vcf_index
    } else {
      inputs[i][0].indexed = false
      // NOTE: using Path instance to avoid NF restrictions on path() process inputs
      inputs[i] << Paths.get('NO_FILE')
    }
  }
  return inputs
}

def prepare_smlv_channel(ch_vcfs) {
  // Pair and correctly order VCFs and indices
  // Input and filtered VCFs must be split first to group correctly
  // Format: [attributes, vcf_one, index_one, vcf_two, index_two]
  ch_vcfs_split = ch_vcfs
    .branch {
      input: ! it[0].filtered
      filtered: it[0].filtered
    }
  ch_vcfs_paired_input = pair_vcf_and_indices(ch_vcfs_split.input)
  ch_vcfs_paired_filtered = pair_vcf_and_indices(ch_vcfs_split.filtered)
  return Channel.empty().mix(ch_vcfs_paired_input, ch_vcfs_paired_filtered)
}

def pair_vcf_and_indices(ch_vcf_and_indices) {
  // Pair and correctly order VCFs and indices
  // Format: [attributes, vcf_one, index_one, vcf_two, index_two]
  ch_result = ch_vcf_and_indices
    // As we cannot directly call groupTuple on Attributes, we construct the group key and place at index 0:
    // Format: [[sample_name, data_source], attributes, vcf_one, index_one, vcf_two, index_two]
    .map {
        def attrs = it[0]
        def values = it[1..-1]
        tuple(groupKey([attrs.sample_name, attrs.data_source], 0), attrs, *values)
    }
    // Now we can collect with groupTuple
    // Format: [
    //             [sample_name, data_source],
    //             [attributes_one, attributes_two],
    //             [vcf_one, vcf_two],
    //             [index_one, index_two]
    //         ]
    .groupTuple()
    .map { group_key, attributes_list, vcfs, vcf_indices ->
      // Get index of first and second file
      def index_one = null
      def index_two = null
      (index_one, index_two) = get_file_order(attributes_list)
      // Check attributes are consistent
      check_attribute_consistency(attributes_list)
      // Use first attribute instance and update
      def attributes = attributes_list[0].clone()
      attributes.run_number = null
      return [
        attributes,
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
    // As we cannot directly call groupTuple on Attributes, we construct the group key and place at index 0:
    // Format: [sample_name, attributes, file]
    .map { attrs, file -> tuple( groupKey(attrs.sample_name, 0), attrs, file ) }
    // Now we can collect with groupTuple
    // Format: [sample_name, [attributes_one, attributes_two], [file_one, file_two]]
    .groupTuple()
    .map { group_key, attributes_list, files ->
      // Get index of first and second file
      def index_one = null
      def index_two = null
      (index_one, index_two) = get_file_order(attributes_list)
      // Check data is consistent
      check_attribute_consistency(attributes_list)
      // Use first attribute instance and update
      attributes = attributes_list[0]
      attributes.run_number = null
      return [
        attributes,
        files[index_one],
        files[index_two],
      ]
    }
  return ch_result
}

def get_file_order(attributes_list) {
  def index_one = null
  def index_two = null
  def run_number_first = attributes_list[0].run_number
  def run_number_second = attributes_list[1].run_number
  if (run_number_first == 'one') {
    assert run_number_second == 'two'
    index_one = 0
    index_two = 1
  } else if (run_number_second == 'one') {
    assert run_number_first == 'two'
    index_one = 1
    index_two = 0
  } else if (run_number_first == null && run_number_second == null) {
    // Allow positions to be null but only if they both are
  } else {
    assert false
  }
  return [index_one, index_two]
}

def check_attribute_consistency(attributes_list) {
  attributes_check = ['sample_name', 'run_type', 'data_source', 'data_type', 'filtered', 'indexed']
  for (attribute_check in attributes_check) {
    def value_one = attributes_list[0][attribute_check]
    def value_two = attributes_list[1][attribute_check]
    assert value_one == value_two
  }
}
