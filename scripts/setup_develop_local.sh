#!/bin/bash
# Link all packages from ~/.local to the source location, for development.
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
./scripts/update_git_hash.py
python setup.py clean config build develop --user --cython $*
