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
