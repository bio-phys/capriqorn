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

"""A set of unit tests of the Capriqorn data processing pipeline code.

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


import sys
from os.path import join as pjoin

import cadishi.util as util
import capriqorn.postproc as postproc_all


def test_strip_virtual_particles_basic(tmpdir):
    h5file = pjoin(tmpdir.dirname, 'merge_virt_particles.h5')
    reader = postproc_all.DummyReader(n_virtual=2, shell=True)
    filtr1 = postproc_all.StripVirtualParticles(source=reader)
    filtr2 = postproc_all.MergeVirtualParticles(source=filtr1)
    writer = postproc_all.H5Writer(source=filtr2, file=h5file)
    writer.dump()
