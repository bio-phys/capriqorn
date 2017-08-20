#!/usr/bin/env python2.7

"""Unit tests to test cadishi.io.hdf5.

Located within Capriqorn due to the depencency of the dummy reader.
"""
# This file is part of the capriqorn package.  See README.rst,
# LICENSE.txt, and the documentation for details.


__author__ = "Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2016 Klaus Reuter"
__license__ = "license_tba"


from cadishi import base
from cadishi import util
from cadishi.io import hdf5
from capriqorn.preproc.io import dummy


do_cleanup = True
h5file = util.scratch_dir() + "test_cadishi_io_hdf5.h5"


def test_h5writer():
    reader = dummy.DummyReader(verbose=True)
    writer = hdf5.H5Writer(source=reader, file=h5file, verbose=True)
    writer.dump()


def test_h5reader():
    reader = hdf5.H5Reader(file=h5file, verbose=True)
    writer = dummy.DummyWriter(source=reader, verbose=True)
    writer.dump()


def test_h5reader_file_list():
    file_list = [h5file, h5file, h5file]
    reader = hdf5.H5Reader(file=file_list, verbose=True)
    writer = dummy.DummyWriter(source=reader, verbose=True)
    writer.dump()


def test_h5reader_shuffle():
    file_list = [h5file]
    reader = hdf5.H5Reader(file=file_list, shuffle=True,
                           verbose=True)
    writer = dummy.DummyWriter(source=reader, verbose=True)
    writer.dump()


def test_h5reader_shuffle_reproducible():
    file_list = [h5file]
    reader = hdf5.H5Reader(file=file_list, shuffle=True,
                           shuffle_reproducible=True, verbose=True)
    writer = dummy.DummyWriter(source=reader, verbose=True)
    writer.dump()


if do_cleanup:
    def test_final_cleanup():
        util.rmrf(util.scratch_dir())
