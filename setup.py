#!/usr/bin/env python3
import setuptools
import sys


import woof_nf


setuptools.setup(
    name='woof-nf',
    version=woof_nf.__version__,
    description='Variant comparison pipeline',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': ['woof_nf=woof_nf.__main__:entry'],
    }
)
