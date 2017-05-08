#!/usr/bin/env python2.7

"""A set of unit tests of the Capriqorn data processing pipeline code.

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
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
        def __init__(self, file, source):
            preproc_io.H5Writer.__init__(
                self, file=file + ".h5", source=source)
else:
    class wrap_writer(preproc_io.ASCIIWriter):
        pass


# --- unit test routines below ---
def test_sphere_filter_body(reader):
    radius = 45.0
    filtre = preproc_filter.Sphere(source=reader, radius=radius)
    func_name = sys._getframe().f_code.co_name
    writer = wrap_writer(out_suffix + func_name, source=filtre)
    writer.dump()


def test_sphere_filter_coreshell(reader):
    radius = 45.0
    shell_width = 3.0
    filtre = preproc_filter.Sphere(
        source=reader, radius=radius, shell_width=shell_width)
    func_name = sys._getframe().f_code.co_name
    writer = wrap_writer(out_suffix + func_name, source=filtre)
    writer.dump()


def test_ellipsoid_filter_body(reader):
    semi_principal_axes = [15.0, 25.0, 30.0]
    filtre = preproc_filter.Ellipsoid(
        source=reader, semi_principal_axes=semi_principal_axes)
    func_name = sys._getframe().f_code.co_name
    writer = wrap_writer(out_suffix + func_name, source=filtre)
    writer.dump()


def test_ellipsoid_filter_coreshell(reader):
    semi_principal_axes = [15.0, 25.0, 30.0]
    shell_width = 3.0
    filtre = preproc_filter.Ellipsoid(
        source=reader, semi_principal_axes=semi_principal_axes, shell_width=shell_width)
    func_name = sys._getframe().f_code.co_name
    writer = wrap_writer(out_suffix + func_name, source=filtre)
    writer.dump()


def test_cuboid_filter_body(reader):
    l_half = [15.0, 25.0, 30.0]
    filtre = preproc_filter.Cuboid(
        source=reader, half_lengths=l_half)
    func_name = sys._getframe().f_code.co_name
    writer = wrap_writer(out_suffix + func_name, source=filtre)
    writer.dump()


def test_cuboid_filter_coreshell(reader):
    l_half = [15.0, 25.0, 30.0]
    shell_width = 3.0
    filtre = preproc_filter.Cuboid(
        source=reader, half_lengths=l_half, shell_width=shell_width)
    func_name = sys._getframe().f_code.co_name
    writer = wrap_writer(out_suffix + func_name, source=filtre)
    writer.dump()


# --- end of unit test routines
if do_clean:
    def test_final_cleanup():
        util.rmrf(util.scratch_dir())
