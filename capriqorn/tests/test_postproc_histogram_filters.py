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


"""A set of unit tests of the Capriqorn post-processing pipeline code.
"""
from __future__ import division


from past.utils import old_div
import sys
import os
import glob
import numpy as np
import cadishi.base as base
import cadishi.util as util
from capriqorn.postproc import io as postproc_io
from capriqorn.postproc import filter as postproc_filter
from capriqorn.testing import FrameCounter, KeepLastFrame


def test_dummy_filter():
    reader = postproc_io.DummyReader()
    filtre = postproc_filter.Dummy(source=reader)
    writer = postproc_io.DummyWriter(source=filtre)
    writer.dump()


def test_average_filter():
    n_tot = 100
    n_avg = 10
    n_bins = 1024
    # create histograms filled with ones
    reader = postproc_io.DummyReader(n_histogram_sets=n_tot, n_bins=n_bins, random=False)
    average = postproc_filter.Average(source=reader, n_avg=n_avg)
    counter = FrameCounter(source=average)
    keeper = KeepLastFrame(source=counter)
    writer = postproc_io.DummyWriter(source=keeper)
    writer.dump()
    # consistency checks
    frame_indices_expected = np.arange(n_avg, n_tot + 1, n_avg)
    frame_indices_measured = np.array(counter.frames)
    assert(counter.count == old_div(n_tot, n_avg))
    assert np.allclose(frame_indices_measured, frame_indices_expected)
    # check the last processed frame
    frm = keeper.last_frame
    keys = frm.get_keys(base.loc_histograms, skip_keys='radii')
    for key in keys:
        histo = frm.get_data(base.loc_histograms + '/' + key)
        assert(np.sum(histo, dtype=np.int) == n_bins)


def test_average_filter_all():
    n_tot = 100
    n_bins = 1024
    reader = postproc_io.DummyReader(n_histogram_sets=n_tot, n_bins=n_bins, random=False)
    average = postproc_filter.Average(source=reader, n_avg='all')
    counter = FrameCounter(source=average)
    keeper = KeepLastFrame(source=counter)
    writer = postproc_io.DummyWriter(source=keeper)
    writer.dump()
    # consistency checks
    assert(counter.count == 1)
    # check the last processed frame
    frm = keeper.last_frame
    keys = frm.get_keys(base.loc_histograms, skip_keys='radii')
    for key in keys:
        histo = frm.get_data(base.loc_histograms + '/' + key)
        assert(np.sum(histo, dtype=np.int) == n_bins)


def test_average_filter_remainder():
    n_tot = 100
    n_avg = 70
    n_bins = 1024
    reader = postproc_io.DummyReader(n_histogram_sets=n_tot, n_bins=n_bins, random=False)
    average = postproc_filter.Average(source=reader, n_avg=n_avg)
    counter = FrameCounter(source=average)
    keeper = KeepLastFrame(source=counter)
    writer = postproc_io.DummyWriter(source=keeper)
    writer.dump()
    # consistency checks
    assert(counter.count == 2)
    # check the last processed frame
    frm = keeper.last_frame
    keys = frm.get_keys(base.loc_histograms, skip_keys='radii')
    for key in keys:
        histo = frm.get_data(base.loc_histograms + '/' + key)
        assert(np.sum(histo, dtype=np.int) == n_bins)
