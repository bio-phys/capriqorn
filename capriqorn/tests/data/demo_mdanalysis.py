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


import MDAnalysis as mda

pdbName = "./protein.pdb.gz"
#trajName = "./protein.xtc"
trajName = "./protein.crdbox.gz"

universe = mda.Universe(pdbName, trajName)
n_frames = len(universe.trajectory)

print("n_frames = ", n_frames)

for ts in universe.trajectory:
    print(ts.frame)

