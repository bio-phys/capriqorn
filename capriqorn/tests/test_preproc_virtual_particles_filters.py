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


"""A set of unit tests of the Capriqorn data processing pipeline code.
"""


import sys
import os
import glob
import cadishi.util as util
import capriqorn.preproc.io as preproc_io
import capriqorn.preproc.filter as preproc_filter
from capriqorn.testing import reader


# output to HDF5, the default ("False") is to output to ASCII files
use_hdf5 = True
# unlink any output files in the end
do_clean = True
out_suffix = util.scratch_dir() + "capriqorn_"


# --- for convenience, wrap the writer of choice
if use_hdf5:
    class wrap_writer(preproc_io.H5Writer):
        def __init__(self, filename, source):
            preproc_io.H5Writer.__init__(
                self, file=filename + ".h5", source=source)
else:
    class wrap_writer(preproc_io.ASCIIWriter):
        pass


# --- unit test routines below ---
def test_virtual_particles_basic(reader):
    vp_method = "lattice"
    vp_xL = 80.0
    vp_xRho = 0.033
    vp_qnoise = True
    filtre = preproc_filter.VirtualParticles(source=reader,
                                             method=vp_method,
                                             x_box_length=vp_xL,
                                             x_density=vp_xRho,
                                             noise=vp_qnoise)
    func_name = sys._getframe().f_code.co_name
    writer = wrap_writer(out_suffix + func_name, source=filtre)
    writer.dump()


# --- end of unit test routines
if do_clean:
    def test_final_cleanup():
        util.rmrf(util.scratch_dir())
