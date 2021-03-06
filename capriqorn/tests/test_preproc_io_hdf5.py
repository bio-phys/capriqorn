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


"""A set of unit tests of the Capriqorn preprocessor HDF5 IO code.
"""


from builtins import range
from six.moves import range
import cadishi.base as base
import cadishi.util as util
import capriqorn.preproc.io as preproc_io
import capriqorn.preproc.filter as preproc_filter

from capriqorn.testing import reader

do_cleanup = True
h5name = util.scratch_dir() + "test_preproc_io_hdf5.h5"
h5tmp = util.scratch_dir() + "test_preproc_io_hdf5_tmp.h5"


# --- tests below ---


def test_H5Writer():
    reader = preproc_io.DummyReader(n_frames=5, n_elems=7, n_atoms=2048)
    writer = preproc_io.H5Writer(h5name, source=reader)
    writer.dump()


def test_H5Reader():
    reader = preproc_io.H5Reader(h5name)
    writer = preproc_io.DummyWriter(source=reader)
    writer.dump()


def test_H5Reader_get_frame():
    reader = preproc_io.H5Reader(h5name)
    frm = reader.get_frame(0)
    for spec in frm.get_keys(base.loc_coordinates):
        crds = frm.get_data(base.loc_coordinates + '/' + spec)
        assert crds.shape == (2048, 3)


def test_H5Reader_trajectory_information():
    reader = preproc_io.H5Reader(h5name)
    ti = reader.get_trajectory_information()
    assert ti.frame_numbers == list(range(1, 6))


def test_H5Writer_gzip():
    reader = preproc_io.DummyReader()
    writer = preproc_io.H5Writer(h5name, source=reader, compression="gzip")
    writer.dump()


def test_MDReader_H5Writer(reader):
    writer = preproc_io.H5Writer(h5name, source=reader)
    writer.dump()


def test_H5Reader_first_last():
    reader = preproc_io.H5Reader(h5name, first=3, last=6)
    writer = preproc_io.H5Writer(h5tmp, source=reader)
    writer.dump()
    # we need to flush the H5 file by closing it before reading from it
    del(reader)
    del(writer)
    reader = preproc_io.H5Reader(h5tmp)  # reader starts numbering from 1
    ti = reader.get_trajectory_information()
    assert ti.frame_numbers == list(range(1, 5))
    util.rm(h5tmp)


if do_cleanup:
    def test_final_cleanup():
        util.rmrf(util.scratch_dir())
