# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
# 
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN 
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

#!/usr/bin/env python2.7

"""A set of unit tests of the Capriqorn post-processing IO code.

This file is part of the Capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


import sys
import os
import glob
import cadishi.util as util
from capriqorn.postproc import io as postproc_io
from capriqorn.postproc import filter as postproc_filter


do_cleanup = True
out_directory = util.scratch_dir()
h5name = out_directory + "histograms.h5"


def test_DummyReader_DummyWriter():
    reader = postproc_io.DummyReader()
    writer = postproc_io.DummyWriter(source=reader)
    writer.dump()


def test_distHistoWriter():
    reader = postproc_io.DummyReader()
    writer = postproc_io.distHistoWriter(source=reader, directory=out_directory,
                                         write_txt=True, verbose=False)
    writer.dump()


def test_distHistoReader():
    reader = postproc_io.distHistoReader(directory=out_directory, verbose=False)
    writer = postproc_io.DummyWriter(source=reader)
    writer.dump()


def test_distHistoReader_step():
    reader = postproc_io.distHistoReader(directory=out_directory,
                                         step=2, verbose=False)
    writer = postproc_io.DummyWriter(source=reader)
    writer.dump()


def test_distHistoReader_first_last():
    reader = postproc_io.distHistoReader(directory=out_directory,
                                         first=2, last=8, verbose=False)
    writer = postproc_io.DummyWriter(source=reader)
    writer.dump()


def test_distHistoReader_first_last_step():
    reader = postproc_io.distHistoReader(directory=out_directory,
                                         first=2, last=8, step=3, verbose=False)
    writer = postproc_io.DummyWriter(source=reader)
    writer.dump()


def test_H5Writer():
    reader = postproc_io.DummyReader()
    writer = postproc_io.H5Writer(source=reader, file=h5name, verbose=False)
    writer.dump()


def test_H5Reader():
    reader = postproc_io.H5Reader(file=h5name, verbose=False)
    writer = postproc_io.DummyWriter(source=reader)
    writer.dump()


def test_H5Reader_H5Writer():
    reader = postproc_io.H5Reader(file=h5name, verbose=False)
    writer = postproc_io.H5Writer(source=reader, file=h5name[:-3] + '_dup' + '.h5')
    writer.dump()


if do_cleanup:
    def test_final_cleanup():
        util.rmrf(out_directory)
