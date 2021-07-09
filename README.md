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
### Docker
A [Docker image](https://hub.docker.com/r/scwatts/woof-nf) for `woof-nf` is available.

### Conda
`woof-nf` is also available as a Conda package:
```bash
conda create \
  --prefix $(pwd -P)/conda_env/ \
  --channel scwatts \
  --channel pdiakumis \
  --channel bioconda \
  --channel conda-forge \
  --channel defaults \
  --yes \
  woof-nf
```

The `circos` Conda package is currently broken. To fix the install run:
```bash
# Activate
conda activate conda_env/
# Apply fix: GD and libwebp; Statistics::Basic (macOS only)
if [[ "$(uname)" == "Darwin" ]]; then
  ln -s ${CONDA_PREFIX}/lib/libwebp.7.dylib ${CONDA_PREFIX}/lib/libwebp.6.dylib
  conda install -y -c bioconda perl-app-cpanminus
  cpan Statistics::Basic
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
  ln -s ${CONDA_PREFIX}/lib/libwebp.so.7 ${CONDA_PREFIX}/lib/libwebp.so.6
else
  echo "error: system appears unsupported, got $(uname) but expected Linux or Darwn" >&2
fi
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

Running locally using Docker to provide dependencies:
```bash
./woof_nf-runner.py \
  --run_dir_one data/first_set/ \
  --run_dir_two data/second_set/ \
  --output_dir output/
  --docker
```

Running locally entirely within Docker (not currently recommended):
```bash
# Paths *must* be absolute
RUN_DIR_ONE=$(pwd -P)/data/run_one/
RUN_DIR_TWO=$(pwd -P)/data/run_two/
OUTPUT_DIR=$(pwd -P)/output/
docker run \
  --mount type=bind,source=${RUN_DIR_ONE},target=/run_one/,readonly \
  --mount type=bind,source=${RUN_DIR_TWO},target=/run_two/,readonly \
  --mount type=bind,source=${OUTPUT_DIR},target=/output/ \
  woof-nf \
  woof \
    --run_dir_one /run_one/ \
    --run_dir_two /run_two/ \
    --output_dir /output/
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
* resume is not currently possible when running entirely within Docker
    - NF work directory option needs to be exposed and set to an non-ephemeral location
* CLI argument checking is incomplete
* not all applicable columns are formatted with commas in report
* report is generated on execution machine i.e. never on AWS
* data subsetting for report is naive; needs improvement
* CNV diff coord data is not currently displayed in report
* tables are sometimes display with inconsistent styling/search box dimensions

## License
Software and code in this repository is under [GNU General Public License
v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) unless otherwise stated.
