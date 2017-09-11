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

import time
import numpy as np
from capriqorn.lib import refstruct
from capriqorn.kernel import c_refstruct

n_xyz = 50000
n_ref = 5000

xyz = np.random.rand(n_xyz, 3)
ref = np.random.rand(n_ref, 3)
R = 0.75

print " Measuring queryDistance() performance ..."
print " n_xyz=" + str(n_xyz) + ", n_ref=" + str(n_ref)

t0 = time.clock()
q_old = refstruct.queryDistance_legacy(xyz, ref, R)
dt = time.clock() - t0
print " * queryDistance_legacy: ", dt

t0 = time.clock()
q_new = refstruct.queryDistance_opt(xyz, ref, R)
dt = time.clock() - t0
print " * queryDistance_opt:    ", dt

t0 = time.clock()
q_acc = c_refstruct.queryDistance(xyz, ref, R)
dt = time.clock() - t0
print " * queryDistance_cython: ", dt

t0 = time.clock()
c_refstruct.queryDistance(xyz, ref, R)
dt = time.clock() - t0
print " * queryDistance:        ", dt

print " Comparing results ..."
assert(np.array_equal(q_new, q_old))
assert(np.array_equal(q_new, q_acc))
print " OK!"
