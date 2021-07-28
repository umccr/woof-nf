# Conda package build instructions
## Build
```bash
# pdiakumis channel provides r-rock, r-woofr
conda build \
  --channel pdiakumis \
  --channel bioconda \
  --channel conda-forge \
  --channel defaults \
  infrastructure/conda/meta.yaml
```

## Upload
```bash
# Find built package filepath from the conda build command above and set
PACKAGE_FP=/usr/local/Caskroom/miniconda/base/conda-bld/noarch/woof-nf-0.2.1-py_0.tar.bz2

# Login and upload package
anaconda login
anaconda upload "${PACKAGE_FP}"
```
