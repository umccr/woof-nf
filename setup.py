#!/usr/bin/env python3
import setuptools
import sys


import comparison_pipeline


setuptools.setup(
    name='Comparison pipeline',
    version=comparison_pipeline.__version__,
    description='Variant comparison pipeline',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': ['comparison_pipeline=comparison_pipeline.__main__:entry'],
    }
)
