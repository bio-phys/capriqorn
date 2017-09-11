#!/usr/bin/env python2.7

# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Preprocessor example pipeline that converts an
MD dataset consisting of PDB and TRJ to HDF5 format.
"""


import os
import sys
import capriqorn.preproc_io as preproc_io
import capriqorn.preproc_filter as preproc_filter

# --- set input files
pdb_in = "protein.pdb.gz"
# traj_in = "protein.xtc"
traj_in = "protein.crdbox.gz"
alias_in = "alias.dat"
# --- set output file
h5_out = "protein.h5"


reader = preproc_io.MDReader(pdbName=pdb_in, trajName=traj_in,
                             aliasName=alias_in)
writer = preproc_io.H5Writer(h5_out, source=reader,
                             compression="gzip", verbose=True)
writer.dump()
