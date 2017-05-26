#!/bin/bash

# disabled, cadishi dependence not yet solved
exit 1

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONDA_BLD_OUTDIR=$DIR/output/
mkdir -p $CONDA_BLD_OUTDIR

export CONDA_BLD_PATH=/tmp/$USER/conda-bld
mkdir -p $CONDA_BLD_PATH

conda build --no-anaconda-upload --output-folder $CONDA_BLD_OUTDIR ./recipe/
