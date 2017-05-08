"""Time-critical routines from <preproc_filter_virtual_particles.py>,
rewritten and accelerated using Cython.

This file is part of the capriqorn package.  See README.rst, LICENSE.txt, and
the documentation for details.
"""


import cython
# from cython.parallel import parallel, prange
import numpy as np
cimport numpy as np
import capriqorn.lib.rotate as rot


FTYPE = np.float64
ctypedef np.float64_t FTYPE_t
ITYPE = np.int
ctypedef np.int_t ITYPE_t


#@cython.boundscheck(False)
def genLattice(gridLength, latticeConstant, noise=False):
    """
    Generate a 3D lattice, optionally with random displacement.
    Serves as a helper function for <preproc_filter_virtual_particles.py>.
    """

    cdef np.ndarray[FTYPE_t, ndim=2] base = np.zeros((3, 3))
    base[0, 0] = latticeConstant
    base[1, 1] = latticeConstant
    base[2, 2] = latticeConstant
    
    cdef FTYPE_t alpha = np.random.uniform(0, 2 * np.pi)
    cdef FTYPE_t beta = np.arccos(np.random.uniform(-1, 1))
    cdef FTYPE_t gamma = np.random.uniform(0, 2 * np.pi)
    
    cdef np.ndarray[FTYPE_t, ndim=2] baseNew = rot.rotate(base, alpha, beta, gamma)
    
    cdef np.ndarray[FTYPE_t, ndim=2] lattice = np.zeros((gridLength ** 3, 3))
    
    cdef FTYPE_t l_half = gridLength / 2
    cdef ITYPE_t idx = 0
    
    cdef ITYPE_t i
    cdef ITYPE_t j
    cdef ITYPE_t k

    # --- original Python code
#     for i in range(gridLength):
#         for j in range(gridLength):
#             for k in range(gridLength):
#                 vec = np.asarray([i, j, k], dtype=np.float) - l_half
#                 lattice[idx] = vec[0] * baseNew[0, :] \
#                                  + vec[1] * baseNew[1, :] \
#                                  + vec[2] * baseNew[2, :]
#                 if noise is True:
#                     lattice[idx] += 0.5 * (np.random.uniform(-1, 1) * baseNew[0, :]
#                                              + np.random.uniform(-1, 1) * baseNew[1, :]
#                                              + np.random.uniform(-1, 1) * baseNew[2, :])
#                 idx += 1
#     offset = np.random.uniform(-latticeConstant / 2., latticeConstant / 2., 3)
#     lattice[:] += offset

    cdef np.ndarray[FTYPE_t, ndim=1] offset = np.random.uniform(-latticeConstant / 2., latticeConstant / 2., 3)
    cdef np.ndarray[FTYPE_t, ndim=2] noize
    
    if noise is True:
        # create randomness in a vectorized way
        noize = np.random.uniform(-0.5, 0.5, (gridLength ** 3, 3))
        for i in range(gridLength):
            for j in range(gridLength):
                for k in range(gridLength):
                    lattice[idx] = (FTYPE(i) - l_half + noize[idx,0]) * baseNew[0] \
                                 + (FTYPE(j) - l_half + noize[idx,1]) * baseNew[1] \
                                 + (FTYPE(k) - l_half + noize[idx,2]) * baseNew[2] \
                                 + offset
                    idx += 1
    else:
        for i in range(gridLength):
            for j in range(gridLength):
                for k in range(gridLength):
                    lattice[idx] = (FTYPE(i) - l_half) * baseNew[0] \
                                 + (FTYPE(j) - l_half) * baseNew[1] \
                                 + (FTYPE(k) - l_half) * baseNew[2] \
                                 + offset
                    idx += 1

    return lattice
