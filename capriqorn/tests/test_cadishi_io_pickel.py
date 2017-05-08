#!/usr/bin/env python2.7

"""Unit tests to test cadishi.base.container and cadishi.pickel.

Even though this file tests some functionality of Cadishi, it is packaged
with capriqorn because it requires dummy.DummyReader()
to have a source for test data.
"""
# This file is part of the Capriqorn package.  See README.rst,
# LICENSE.txt, and the documentation for details.


__author__ = "Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2016 Klaus Reuter"
__license__ = "license_tba"


import glob
from cadishi import base
from cadishi import util
from cadishi.io import pickel
from capriqorn.preproc.io import dummy


do_cleanup = True
h5file = util.scratch_dir() + "test_cadishi_io_pickle_"


def test_picklewriter():
    reader = dummy.DummyReader(verbose=True, n_frames=3)
    writer = pickel.PickleWriter(source=reader, file=h5file, verbose=True)
    writer.dump()


def test_picklereader():
    reader = pickel.PickleReader(file=h5file, first=1, last=3, verbose=True)
    writer = dummy.DummyWriter(source=reader, verbose=True)
    writer.dump()


if do_cleanup:
    def test_final_cleanup():
        for file in glob.glob(h5file + '*'):
            util.rmrf(util.scratch_dir())
