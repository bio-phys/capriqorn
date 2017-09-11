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


"""Compare two HDF5 files containing distance histograms.
The distance histograms are NumPy arrays.
"""


import os
import sys
import itertools
import glob
import numpy as np
import argparse

from cadishi import base
from cadishi import util
from ..postproc import io


def configure_cli(subparsers):
    """Attach a parser (specifying command name and flags) to the argparse subparsers object."""
    parser = subparsers.add_parser('compare', help='compare histograms of two HDF5 files')
    parser.add_argument('files', nargs=argparse.REMAINDER, help='HDF5 files', metavar='file1.h5 file2.h5')
    parser.set_defaults(func=main)


def main(pargs):
    args = vars(pargs)
    file_list = args['files']

    assert(len(file_list) == 2)

    print(util.SEP)

    # --- tolerance used by util.compare_approximately
    tolerance_val = 1.e-3

    reader_1 = postproc_io.H5Reader(filename=file_list[0], verbose=False)
    reader_2 = postproc_io.H5Reader(filename=file_list[1], verbose=False)

    # --- iterate through both the generators (== readers) simultaneously
    for (container_1, container_2) in itertools.izip(reader_1.next(), reader_2.next()):
        hs_1 = container_1.get_data(base.loc_histograms)
        hs_2 = container_2.get_data(base.loc_histograms)
        hsk_1 = sorted(hs_1.keys())
        hsk_2 = sorted(hs_2.keys())
        hsk_1.remove('radii')
        hsk_2.remove('radii')
        assert(hsk_1 == hsk_2)
        # ---
        for key in hsk_1:
            h1 = hs_1[key]
            h2 = hs_2[key]
            try:
                util.compare_approximately(h1, h2)
            except AssertionError:
                np.savetxt('h1.dat', h1)
                np.savetxt('h2.dat', h2)
                print " FAIL"
                sys.exit(1)

    print " OK!"
    print(util.SEP)
