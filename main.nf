#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

// Inputs
vcf_first = create_input_vcf_channel('first', 'data/gs_one.vcf.gz')
vcf_two = create_input_vcf_channel('second', 'data/gs_two.vcf.gz')
vcfs = Channel.empty().mix(vcf_first, vcf_two)

// Helper functions
def create_input_vcf_channel(vcf_position, filepath) {
  return Channel.fromPath(filepath)
    .map { [vcf_position, it.getSimpleName(), it] }
}

// NOTE: we could include indices here as well
def arrange_channel(channel) {
  channel.toList().map { d ->
    // This should be done cleanly in a single loop
    // Clearly define case and limits thereof
    first_index = d.collect { it[0] }.indexOf('first')
    second_index = (first_index == 0) ? 1 : 0
    // Assertion here
    [
      d[first_index][1], // first sample_name
      d[second_index][1], // second sample_name
      d[first_index][2], // first vcf
      d[second_index][2], // second vcf
    ]
  }
}

// Processes
process variants_pass {
  publishDir "${params.output_dir}/1_variants_pass/"

  input:
  tuple val(vcf_position), val(sample_name), path(vcf)

  output:
  tuple val(vcf_position), val("${sample_name}_pass"), path('*.vcf')

  script:
  """
  {
    bcftools view -h "${vcf}";
    bcftools view -Hf .,PASS "${vcf}" | sort -k1,1V -k2,2n;
  } | \
    bcftools view -Oz \
    > "${sample_name}_pass.vcf"
  """
}

process variants_intersect {
  publishDir "${params.output_dir}/2_variants_intersect/${sample_name}"

  input:
  tuple val(sname_one), val(sname_two), path(vcf_one), path(vcf_two)

  output:
  tuple val(sample_name), path('*vcf')

  script:
  sample_name = "${sname_one}__${sname_two}"
  """
  tabix "${vcf_one}"
  tabix "${vcf_two}"
  bcftools isec "${vcf_one}" "${vcf_two}" -p ./
  """
}

// Workflow
workflow {
  // Filter variants
  vcfs_pass = variants_pass(vcfs)

  vcfs_pass.toList().view()
  vcfs.toList().view()

  // NOTE: here is an appropriate point to index vcfs
  // This means we would be at:
  //   [vcf_position, sample_name, vcf, vcf_index]
  //
  // And the arrange_channe function needs to be modified to:
  //  d[first_index][1], // first sample_name
  //  d[second_index][1], // second sample_name
  //  d[first_index][2], // first vcf
  //  d[first_index][3], // first vcf (index_
  //  d[second_index][2], // second vcf
  //  d[second_index][3], // second vcf (index)
  //
  // Following, the input for variants_intersect needs to be updated as well

  // Now arrange
  vcfs_squashed = arrange_channel(vcfs)
  vcfs_pass_squashed = arrange_channel(vcfs_pass)
  vcfs_all_squashed = Channel.empty().mix(vcfs_squashed, vcfs_pass_squashed)

  vcfs_all_squashed.toList().view()

  vcfs_all_intersect = variants_intersect(vcfs_all_squashed)

  // Count number of variants(?) in vcfs (input, pass, intersect)
}
