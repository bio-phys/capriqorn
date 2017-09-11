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


"""A set of unit tests of the Capriqorn preprocessor MDAnalysis IO code.
"""


import numpy as np
import cadishi.base as base
import capriqorn.preproc.io as preproc_io
import capriqorn.preproc.filter as preproc_filter
from capriqorn.testing import data, FrameCounter
import pytest


@pytest.mark.parametrize('first, last', [[3, 6],
                                         [1, 8],
                                         [None, 3],
                                         [3, None],
                                         [None, None]])
def test_MDReader_first_last(data, first, last):
    reader = preproc_io.MDReader(pdb_file=data["protein.pdb.gz"],
                                 trajectory_file=data["protein.crdbox.gz"],
                                 alias_file=data["alias.dat"],
                                 first=first, last=last)
    counter = FrameCounter(source=reader)
    writer = preproc_io.DummyWriter(source=counter)
    writer.dump()

    if first is None:
        first = 1
    if last is None:
        last = reader.universe.trajectory.n_frames

    n_frames = last - first + 1
    assert counter.count == n_frames
    assert np.allclose(np.array(counter.frames), np.arange(first, last + 1))


@pytest.mark.parametrize('first, last, step', [[3, 6, 2],
                                               [1, 8, 3],
                                               [None, 3, 2],
                                               [3, None, 2],
                                               [None, None, 3]])
def test_MDReader_first_last_step(data, first, last, step):
    reader = preproc_io.MDReader(pdb_file=data["protein.pdb.gz"],
                                 trajectory_file=data["protein.crdbox.gz"],
                                 alias_file=data["alias.dat"],
                                 first=first, last=last, step=step)
    counter = FrameCounter(source=reader)
    writer = preproc_io.DummyWriter(source=counter)
    writer.dump()

    if first is None:
        first = 1
    if last is None:
        last = reader.universe.trajectory.n_frames

    frame_indices_expected = np.arange(first, last + 1, step)
    frame_indices_measured = np.array(counter.frames)

    assert counter.count == len(frame_indices_expected)
    assert np.allclose(frame_indices_measured, frame_indices_expected)
