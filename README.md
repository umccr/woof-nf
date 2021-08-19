&nbsp;
&nbsp;
&nbsp;
<p align="center">
🚧🚨 <em>Under development</em> 🚨🚧
</p>

# woof-nf
`woof-nf` evaluates the concordance between genomic variants called from the same sample by
different methods. This tool is particularly useful for understanding the practical impacts of
changes and updates made to variant calling pipelines, and for detecting the introduction of
regressions.

The core logic of `woof-nf` has been ported from the [woof](https://github.com/pdiakumis/woof)
pipeline.

## Table of contents
* [Installation](#installation)
* [Usage](#usage)
* [Outputs](#outputs)
* [Requirements](#requirements)
* [Known Issues](#known-issues)
* [License](#license)

## Installation
Using Conda to install `woof-nf` is recommended. A [Docker
image](https://hub.docker.com/r/scwatts/woof-nf) is also available though it is primarily used for
AWS Batch execution. While possible to run `woof-nf` partially or entirely within the Docker
container locally, doing so is not fully supported.

### Conda
Simply create a new Conda environment and install `woof-nf`:
```bash
conda create \
  --prefix $(pwd -P)/conda_env/ \
  --channel umccr \
  --channel bioconda \
  --channel conda-forge \
  --channel defaults \
  --yes \
  woof-nf
```

### Requirements for AWS
There is an AWS plugin packaged with Nextflow that allows execution of tasks through AWS Batch. The
following AWS infrastructure are required:
1. Batch job queue,
2. Batch compute environment, and
3. Batch instance role

For specifics and example CloudFormation template see `infrastructure/aws_nextflow_batch.yaml`. Note
that the security groups and subnets referenced in this file are specific to the UMCCR AWS dev
account and are managed by Terraform.

Additionally, you will also need to install `aws-cli`. This can be obtained through Conda or
[installed manually](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html).

## Usage
Execute and run jobs locally:
```bash
./woof_nf-runner.py \
  --run_dir_one data/first_set/ \
  --run_dir_two data/second_set/ \
  --output_dir output/
```

Execute locally, run jobs on AWS:
```bash
./woof_nf-runner.py \
  --run_dir_one data/first_set/ \
  --run_dir_two data/second_set/ \
  --output_dir s3://bucket-name/output/ \
  --executor aws
```

Execute locally, run jobs on AWS with S3 inputs and outputs:
```bash
./woof_nf-runner.py \
  --run_dir_one s3://bucket-name/first_set/ \
  --run_dir_two s3://bucket-name/second_set/ \
  --output_dir s3://bucket-name/output/ \
  --executor aws
```
> When running jobs on AWS with an S3 output directory, a local directory will be created to store configuration and log
> files. The directory is uniquely named as `nf_[0-9a-z]{8}` and can deleted after the successful completion of the pipeline.

> AWS configuration is currently hard coded in `woof_nf/aws.py`.

## Outputs
The `woof-nf` output directory contains:
* a report detailing results (`report.html`),
* individual directories for sample outputs (further details below),
* the pipeline log (`pipeline_log.txt`),
* a copy of the pipeline configuration (`nextflow.config`), and
* the list of input files (`input_files`)

Here is the directory structure of an example output:
```text
output/
├── 2016_249_17_MH_P033__CCR170115b_MH17T002P033/
├── B_ALL_Case_10__MDX190025_B_ALL_Case_10T/
├── COLO829_1__Colo829/
├── COLO829_2__Colo829_60pc/
├── CUP-Pairs8__PRJ180660_8_DNA009529_FFPE/
├── SEQC-II-50pc__SEQC-II_Tumor_50pc/
├── SFRC01073__PRJ180598_SFRC01073-S2T/
├── input_files.tsv
├── nextflow.config
├── pipeline_log.txt
└── report.html
```

Each sample directory contains three subdirectories, and you can find data presented in the
`report.html` file in the appropriate sample subdirectory. Here is the directory structure of one
sample from the example output:
```text
output/COLO829_1__Colo829/
├── copy_number_variants
│   ├── cn_diff.tsv
│   └── cn_diff_coord.tsv
├── small_variants
│   ├── 1_filtered_vcfs/
│   ├── 2_variants_intersect/
│   ├── 3_comparison/
│   └── counts.tsv
└── structural_variants
    ├── circos/
    ├── eval_metrics.tsv
    └── fpfn.tsv
```

## Requirements
General:
* Python ≥3.6
* BCFtools
* Circos
* Nextflow
* R

R packages:
* bedr
* DT
* glue
* kableextra
* [rock](https://github.com/pdiakumis/rock/)
* tidyverse
* [woofr](https://github.com/pdiakumis/woofr) (currently only required for external data)

Python packages:
* boto3

Optional requirements:
* aws-cli (AWS execution only)
* Docker (local Docker execution only)

## Known Issues
* for bcbio on a single tumour ensemble VCF is currently compared, even if there are multiple
* file paths displayed in report are absolute and may represent paths on Batch instance
* report is required to process/compute data; all should be pre-computed only requiring render
* not all applicable columns are formatted with commas in report
* CNV diff coord data is not currently displayed in report

## License
Software and code in this repository is under [GNU General Public License
v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) unless otherwise stated.
