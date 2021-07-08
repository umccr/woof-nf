#!/usr/bin/env python3
import setuptools
import sys


import woof_nf


setuptools.setup(
    name='woof_nf',
    version=woof_nf.__version__,
    description='Variant comparison pipeline',
    packages=['woof_nf'],
    # Use MANIFEST.in to recursively glob and include files in ./woof_nf/workflow/
    include_package_data=True,
    entry_points={
        'console_scripts': ['woof=woof_nf.__main__:entry'],
    }
)
