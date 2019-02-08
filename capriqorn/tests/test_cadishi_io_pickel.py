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


"""Unit tests to test cadishi.base.container and cadishi.pickel.

Even though this file tests some functionality of Cadishi, it is packaged with
capriqorn because it requires dummy.DummyReader() to have a source for test
data.
"""


import glob
from cadishi import base
from cadishi import util
from cadishi.io import pickel
from capriqorn.preproc.io import dummy


do_cleanup = True
tmpfile = util.scratch_dir() + "test_cadishi_io_pickle_"


def test_picklewriter():
    reader = dummy.DummyReader(verbose=True, n_frames=3)
    writer = pickel.PickleWriter(source=reader, file=tmpfile, verbose=True)
    writer.dump()


def test_picklereader():
    reader = pickel.PickleReader(file=tmpfile, first=1, last=3, verbose=True)
    writer = dummy.DummyWriter(source=reader, verbose=True)
    writer.dump()


if do_cleanup:
    def test_final_cleanup():
        for file in glob.glob(tmpfile + '*'):
            util.rmrf(util.scratch_dir())
