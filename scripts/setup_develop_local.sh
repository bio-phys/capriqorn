#!/bin/bash

#
# Link all packages from ~/.local to the source location, for development.
#

python setup.py clean config build develop --user --cython $*

