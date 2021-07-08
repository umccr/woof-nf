&nbsp;
&nbsp;
&nbsp;
<p align="center">
🚧🚨 <em>Incomplete - Under development</em> 🚨🚧
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
It is recommended that Conda is used for installation and provisioning of dependencies:
```bash
# Create a Conda environment and install mamba
conda create \
    --prefix $(pwd -P)/conda_env/ \
    --channel conda-forge \
    --channel defaults \
    --yes \
    mamba

# Activate the environment and install dependencies
conda activate conda_env/
mamba install \
    --file infrastructure/conda_env.txt \
    --channel pdiakumis \
    --channel bioconda \
    --channel conda-forge \
    --channel defaults \
    --yes
```

> I intend to update the Docker image so it also contains the pipeline itself to allow another mode
> execution and remove Nextflow as a dependency

Alternatively you can use the `woof-nf` [Docker image](https://hub.docker.com/r/scwatts/woof-nf),
provided you have Docker and Nextflow already installed.

### macOS addendum
The Conda `circos` package is currently broken on macOS. To fix the install run:
```bash
# Apply fix for GD and libwebp
ln -s ${CONDA_PREFIX}/lib/libwebp.7.dylib ${CONDA_PREFIX}/lib/libwebp.6.dylib

# Circos installed via conda also requires manual install of Statistics::Basic
mamba install -y -c bioconda perl-app-cpanminus
cpan Statistics::Basic
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
Running locally:
```bash
./woof_nf-runner.py \
  --run_dir_one data/first_set/ \
  --run_dir_two data/second_set/ \
  --output_dir output/
```

Running locally with Docker:
```bash
./woof_nf-runner.py \
  --run_dir_one data/first_set/ \
  --run_dir_two data/second_set/ \
  --output_dir output/
  --docker
```

Running on AWS:
```bash
./woof_nf-runner.py \
  --run_dir_one data/first_set/ \
  --run_dir_two data/second_set/ \
  --output_dir output/
  --executor aws \
  --s3_bucket s3://bucket-name/object-key/
```

Note that AWS configuration is currently hard coded in `woof_nf/aws.py`.

## Outputs
The output directory contains:
* a report detailing results (`report.html`),
* individual directories for sample outputs (further details below),
* the pipeline log (`pipeline_log.txt`),
* a copy of the pipeline configuration (`nextflow.config`), and
* the list of input files (`input_files`)

Here is the directory structure of an example output:
```text
output/
├── 2016_249_17_MH_P033__CCR170115b_MH17T002P033
├── B_ALL_Case_10__MDX190025_B_ALL_Case_10T
├── COLO829_1__Colo829
├── COLO829_2__Colo829_60pc
├── CUP-Pairs8__PRJ180660_8_DNA009529_FFPE
├── SEQC-II-50pc__SEQC-II_Tumor_50pc
├── SFRC01073__PRJ180598_SFRC01073-S2T
├── input_files.tsv
├── nextflow.config
├── pipeline_log.txt
└── report.html
```

Each sample directory contains three directories, which are self-explanatory. You can find data
presented in the `report.html` file in the appropriate sample directory. Here is the directory
structure of one sample from the example output:
```text
output/COLO829_1__Colo829/
├── copy_number_variants
│   ├── cn_diff.tsv
│   └── cn_diff_coord.tsv
├── small_variants
│   ├── 1_filtered_vcfs
│   ├── 2_variants_intersect
│   ├── 3_comparison
│   └── counts.tsv
└── structural_variants
    ├── circos
    ├── eval_metrics.tsv
    └── fpfn.tsv
```

## Requirements
Mandatory requirements:
* Python ≥3.6
* BCFtools
* Circos
* Nextflow
* R

Mandatory R packages:
* bedr
* DT
* glue
* kableextra
* [rock](https://github.com/pdiakumis/rock/)
* tidyverse
* [woofr](https://github.com/pdiakumis/woofr) (currently only required for external data)

Optional requirements:
* aws-cli (AWS execution only)
* Docker (local Docker execution only)

## Known Issues
* report is required to process/compute data; all should be pre-computed only requiring render
* AWS execution can take s3:// URIs but this isn't currently allowable through the wrapper script
* CLI argument checking is incomplete
* not all applicable columns are formatted with commas in report
* report is generated on execution machine i.e. never on AWS
* data subsetting for report is naive; needs improvement
* CNV diff coord data is not currently displayed in report
* tables are sometimes display with inconsistent styling/search box dimensions

## License
Software and code in this repository is under [GNU General Public License
v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) unless otherwise stated.
