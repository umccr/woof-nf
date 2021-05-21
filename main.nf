#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

// Inputs
ch_vcf_one = file('data/gs_one.vcf.gz')
ch_vcf_two = file('data/gs_two.vcf.gz')
ch_vcfs_input = Channel.fromList([
  ['one', ch_vcf_one],
  ['two', ch_vcf_two],
])

// Processes
process variants_pass {
  publishDir "${params.output_dir}/1_variants_pass/"

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_position), path(vcf)

  output:
  tuple val(vcf_position), path('*.vcf.gz')

  script:
  def sample_name = vcf.getSimpleName()
  """
  {
    bcftools view -h "${vcf}";
    bcftools view -Hf .,PASS "${vcf}" | sort -k1,1V -k2,2n;
  } | \
    bcftools view -Oz \
    > "${sample_name}_pass.vcf.gz"
  """
}

process index_vcf {
  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_type), val(vcf_position), path(vcf)

  output:
  tuple val(vcf_type), val(vcf_position), path('*.tbi')

  script:
  """
  tabix "${vcf}"
  """
}

process variants_intersect {
  publishDir "${params.output_dir}/2_variants_intersect/${sample_name}"

  container 'quay.io/biocontainers/bcftools'

  input:
  tuple val(vcf_type), path(vcf_one), path(index_one), path(vcf_two), path(index_two)

  output:
  tuple val(vcf_type), val(sample_name), path('*vcf')

  script:
  sample_name = "intersect__${vcf_one.getSimpleName()}__${vcf_two.getSimpleName()}"
  """
  bcftools isec "${vcf_one}" "${vcf_two}" -p ./
  """
}

process count_variants {
  publishDir "${params.output_dir}/3_variant_counts/${subdir}"

  container 'public.ecr.aws/amazonlinux/amazonlinux:latest'

  input:
  tuple val(subdir), path(vcf)

  output:
  path('*tsv')

  script:
  """
  variant_count=\$(gzip -cd "${vcf}" | sed '/^##/d' | wc -l)
  echo -e "${vcf.getSimpleName()}\t\${variant_count}" > "${vcf.getSimpleName()}.tsv"
  """
}

// Workflow
workflow {
  // Filter variants
  ch_vcfs_pass = variants_pass(ch_vcfs_input)

  // Tag inputs to track and re-pair downstream
  ch_vcfs = Channel.empty().mix(
    Channel.value('pass').combine(ch_vcfs_pass),
    Channel.value('input').combine(ch_vcfs_input)
  )

  // Index
  ch_vcfs_indices = index_vcf(ch_vcfs)

  // Pair and sort VCFs and corresponding indices
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

  // Intersect
  ch_vcfs_intersects = variants_intersect(ch_vcfs_indexed)

  // Variant counts
  ch_vcfs_to_count = Channel.empty().mix(
    ch_vcfs.map { [it[0], it[2]] },
    ch_vcfs_intersects.flatMap { d ->
      d[2].collect { dd -> ["${d[0]}_intersect", dd] }
    }
  )
  count_variants(ch_vcfs_to_count)
}
