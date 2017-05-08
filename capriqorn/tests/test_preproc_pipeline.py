#!/usr/bin/env python2.7

"""A set of unit tests of the Capriqorn preprocessor pipeline code.

This file is part of the Capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


__author__ = "Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2016 Klaus Reuter"
__license__ = "license_tba"


import numpy as np
import cadishi.base as base
import cadishi.util as util
import capriqorn.preproc.io as preproc_io
import capriqorn.preproc.filter as preproc_filter

from capriqorn.testing import reader

do_cleanup = True
h5name = util.scratch_dir() + "test_preproc_pipeline.h5"


def test_simple_pipeline():
    reader = preproc_io.DummyReader()
    filtre = preproc_filter.Dummy(source=reader)
    writer = preproc_io.DummyWriter(source=filtre)
    writer.dump()


def test_xyz_pipeline():
    reader = preproc_io.DummyReader()
    filtre = preproc_filter.XYZ(source=reader, output_directory=util.scratch_dir())
    writer = preproc_io.DummyWriter(source=filtre)
    writer.dump()


def test_sphere_filter_pipeline_query_meta(reader):
    filtre = preproc_filter.Sphere(source=reader, radius=45.0)
    for frm in filtre.next():
        assert isinstance(frm, base.Container)
        # --- query some existing and non existing entries
        assert isinstance(frm.query_meta('Sphere'), dict)
        assert (frm.query_meta('Sphere/radius') == 45.0)
        assert (frm.query_meta('Sphere/krampus') is None)


def test_sphere_filter_pipeline(reader):
    filtre = preproc_filter.Sphere(source=reader, radius=45.0)
    writer = preproc_io.H5Writer(h5name, source=filtre)
    writer.dump()


def test_trajectory_information_radius():
    reader = preproc_io.H5Reader(h5name)
    ti = reader.get_trajectory_information()
    # --- given the previous test of the sphere filter, rmax must be set to 90.0
    assert (np.fabs(ti.get_pipeline_parameter('r_max') - 90.0) <= np.finfo(float).eps)


if do_cleanup:
    def test_final_cleanup():
        util.rmrf(util.scratch_dir())
