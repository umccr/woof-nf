#!/bin/bash
# Conda currently does not create a valid install. Problems specifically relate to circos.
#   - circos dependency GD expects libwebp.6 but Conda installs libwebp.7
#   - circos dependency Statistics::Basic is not correctly installed on macOS
# Apply fixes
if [[ "$(uname)" == "Darwin" ]]; then
  ln -s ${PREFIX}/lib/libwebp.7.dylib ${PREFIX}/lib/libwebp.6.dylib
  conda install -y -c bioconda perl-app-cpanminus
  cpan Statistics::Basic
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
  ln -s ${PREFIX}/lib/libwebp.so.7 ${PREFIX}/lib/libwebp.so.6
else
  echo "error: system appears to be unsupported, got $(uname) but expected Linux or Darwn" >&2
fi
