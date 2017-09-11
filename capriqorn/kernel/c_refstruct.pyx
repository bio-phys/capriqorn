# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

"""Time-critical routines from preproc_filter_refstruct.py, rewritten using Cython.
"""


import cython
# from cython.parallel import parallel, prange
import numpy as np
cimport numpy as np
from libc.math cimport sqrt


DTYPE = np.float64
FTYPE = np.float32
ctypedef np.float64_t DTYPE_t
ctypedef np.float32_t FTYPE_t
ITYPE = np.int
ctypedef np.int_t ITYPE_t


@cython.boundscheck(False)
@cython.wraparound(False)
def queryDistance(np.ndarray[DTYPE_t, ndim=2] xyz, np.ndarray[DTYPE_t, ndim=2] ref, double R):
    """Check which atoms in xyz lie within a radius R of any reference
    atom.

    Reimplementation of the queryDistance() function from preproc_filter_refstruct.py.
    Much faster. Use <perf_preproc_filter_refstruct.py> to measure the performance.

    Parameters
    ----------
    xyz : array_like (n_atoms, n_dim)
        atoms positions
    ref : array_like (n_atoms, n_dim)
        Reference atoms positions
    R : float
        distance to any atoms

    Returns
    -------
    query : ndarray (n_atoms)
        boolean array showing which particle are close to ref
    """
    cdef np.ndarray mask = np.zeros(xyz.shape[0], dtype=bool)
    cdef ITYPE_t n_xyz = xyz.shape[0]
    cdef ITYPE_t n_ref = ref.shape[0]
    cdef ITYPE_t i
    cdef ITYPE_t j
    cdef ITYPE_t k
    cdef DTYPE_t d
    cdef DTYPE_t dx
    cdef DTYPE_t Rsq

    Rsq = R*R

    for i in range(n_xyz):
        for j in range(n_ref):
            d = 0.0
            for k in range(3):
                dx = xyz[i,k] - ref[j,k]
                d = d + dx*dx
            #if (sqrt(d) < R):
            if (d < Rsq):
                mask[i] = True
                break
    return mask
