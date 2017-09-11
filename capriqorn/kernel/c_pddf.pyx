# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

"""Time-critical routines from pddf.py, rewritten using Cython.
"""


import cython
# from cython.parallel import parallel, prange
import numpy as np
cimport numpy as np
from libc.math cimport exp
from libc.math cimport lrint
from libc.math cimport sqrt
from libc.math cimport M_PI


FTYPE = np.float64
ctypedef np.float64_t FTYPE_t
ITYPE = np.int
ctypedef np.int_t ITYPE_t


# inline function used by FT1 (see below), original implementation in formFactor.py
@cython.cdivision(True)
cdef inline FTYPE_t FT1Func(double a, double b, double rSqr):
    """
    Calculate: 2/pi Int[ f^2(q) sin(qr) (qr) dq = a r^2/(2 sqrt(pi b^3)) exp(-r^2/(4b))
    """
    cdef FTYPE_t val
    if b > 0.0:
        # val = a * rSqr / (2. * math.sqrt(math.pi * b * b * b)) * math.exp(-rSqr / (4. * b))
        val = a * rSqr / (2. * sqrt(M_PI * b * b * b)) * exp(-rSqr / (4. * b))
        return val
    else:
        return 0.


# inline function used by pddf, original implementation in formFactor.py
@cython.boundscheck(False)
cdef inline FTYPE_t FT1(paramList, double rSqr):
    """
    """
    cdef np.ndarray[FTYPE_t, ndim=2] param = np.asarray(paramList, dtype=FTYPE)
    cdef ITYPE_t i
    cdef ITYPE_t i_min = 0
    cdef ITYPE_t i_max = param.shape[1]
    cdef FTYPE_t val = 0.
    # ---
    for i in range(i_min, i_max):
        val += FT1Func(param[0][i], param[1][i], rSqr)
    return val


@cython.boundscheck(False)
def getPartCharFunc1(partDHisto, key, paramProd, rArray, double drPrime, double delta):
    """Calculates intra-atom contributions.
    """
    # partCF=np.zeros((len(rArray), 2))
    # partCF[:,0]=rArray[:]
    cdef np.ndarray[FTYPE_t, ndim=2] partCF = np.zeros((len(rArray), 2), dtype=FTYPE)
    partCF[:,0] = np.asarray(rArray[:], dtype=FTYPE)
    param = paramProd[key]
    elements = key.split(",")
    cdef FTYPE_t NMean = partDHisto[key][0,1]
    # print "NMean("+key+") =", NMean
    partCF[0,1] += NMean*param[0][0]
    # print "param[0][0]=", param[0][0]
    cdef FTYPE_t dr = drPrime #DANGER
    cdef ITYPE_t i
    cdef ITYPE_t i_min = 1
    cdef ITYPE_t i_max = partCF.shape[0]
    cdef FTYPE_t r
    cdef FTYPE_t r_sqr
    # ---
    for i in range(i_min, i_max):
        r = partCF[i,0]
        # if ((i-1) % 100 == 0): print " r =", r
        r_sqr = r*r
        partCF[i,1] += NMean * FT1(param, r_sqr)
    return partCF


# pddf.getPartCharFunc2() using Cython -- 25x faster
@cython.cdivision(True)
@cython.boundscheck(False)
def getPartCharFunc2(partDHisto, key, paramProd, rArray, double drPrime, double delta):
    """
    Calculates inter-atom contributions to the EPDDF for a partial distance histogram.

    @param partDHisto Partial distance histogram.
    @param key string Representing pair of particle species.
    @param paramProd Parameter dictionary for products of form factors.
    @param rArray Array of r-values at which characteristic function is evaluated.
    @param drPrime Interval size in r'. At r' the partial histtogram is evaluated.
    @param delta Interval size for integration in r'. The \f$c_{ij}(r,r')\f$ are
                 evaluated within the bin at r' at sub-intevals delta.
    """
    param = paramProd[key]
    elements = key.split(",")
    NMean = partDHisto[key][0,1]
    # print "Running capriqorn_accelerate.getPartCharFunc2() ..."
    # print "NMean("+key+") =", NMean
    cdef np.ndarray[FTYPE_t, ndim=2] partCF = np.zeros((len(rArray), 2), dtype=FTYPE)
    partCF[:,0] = np.asarray(rArray[:], dtype=FTYPE)
    cdef ITYPE_t i
    cdef ITYPE_t i_min = 1
    cdef ITYPE_t i_max = partCF.shape[0]
    cdef np.ndarray[FTYPE_t, ndim=1] a = np.asarray(param[0][1:], dtype=FTYPE)
    cdef np.ndarray[FTYPE_t, ndim=1] b = np.asarray(param[1][1:], dtype=FTYPE)
    cdef np.ndarray[FTYPE_t, ndim=1] fac = a/(2.*np.sqrt(b*np.pi))
    cdef np.ndarray[FTYPE_t, ndim=1] facEx = 1./(4.*b)
    cdef np.ndarray[FTYPE_t, ndim=2] partDHisto_key = np.asarray(partDHisto[key], dtype=FTYPE)
    cdef ITYPE_t j
    cdef ITYPE_t j_min = 1
    cdef ITYPE_t j_max = partDHisto_key.shape[0]
    cdef FTYPE_t dr = drPrime #DANGER
    cdef FTYPE_t r
    cdef FTYPE_t rr
    cdef FTYPE_t tmp
    cdef FTYPE_t rPrime
    cdef FTYPE_t val
    cdef FTYPE_t drPrime_inv = 1./drPrime
    cdef FTYPE_t fac_val
    cdef FTYPE_t rr_min
    cdef FTYPE_t rr_max
    cdef ITYPE_t k
    cdef ITYPE_t k_min = 0
    cdef ITYPE_t k_max = fac.shape[0]
    cdef FTYPE_t tmp_sum
    # --- OpenMP-parallel code ---
    # It appears that parallelization is not efficient due to insufficient work!
    #
    # with nogil, parallel():
    #     for i in prange(i_min, i_max, schedule='dynamic'):
    #         r = partCF[i,0]
    #         tmp = 0.
    #         fac_val = r*delta*drPrime_inv
    #         for j in range(j_min, j_max):
    #             rPrime = partDHisto_key[j,0]
    #             val = partDHisto_key[j,1]
    #             if (val != 0.) and ((rPrime-r)**2 < 9.): #MODI
    #                 val = val * fac_val
    #                 # for rr in np.arange(rPrime-0.5*(drPrime-delta), rPrime+0.5*drPrime, delta, dtype=FTYPE):
    #                 rr_min = rPrime-0.5*(drPrime-delta)
    #                 rr_max = rPrime+0.5*drPrime
    #                 rr = rr_min
    #                 while (rr < rr_max):
    #                     # tmp += val/rr * (fac*(np.exp(-(r-rr)**2 * facEx) - np.exp(-(r+rr)**2 * facEx))).sum()
    #                     tmp_sum = 0.
    #                     for k in range(k_min, k_max):
    #                         tmp_sum = tmp_sum + fac[k] * (exp(-(r-rr)**2 * facEx[k]) - exp(-(r+rr)**2 * facEx[k]))
    #                     tmp = tmp + val/rr * tmp_sum
    #                     rr = rr + delta
    #         partCF[i,1] = partCF[i,1] + tmp
    # --- sequential code ---
    for i in range(i_min, i_max):
        r = partCF[i,0]
        # if ((i-1) % 100 == 0): print " r =", r
        tmp = 0.
        fac_val = r*delta*drPrime_inv
        for j in range(j_min, j_max):
            rPrime = partDHisto_key[j,0]
            val = partDHisto_key[j,1]
            if (val != 0.) and ((rPrime-r)**2 < 9.): #MODI
                val *= fac_val
                # for rr in np.arange(rPrime-0.5*(drPrime-delta), rPrime+0.5*drPrime, delta, dtype=FTYPE):
                rr_min = rPrime-0.5*(drPrime-delta)
                rr_max = rPrime+0.5*drPrime
                rr = rr_min
                while (rr < rr_max):
                    # tmp += val/rr * (fac*(np.exp(-(r-rr)**2 * facEx) - np.exp(-(r+rr)**2 * facEx))).sum()
                    tmp_sum = 0.
                    for k in range(k_min, k_max):
                        tmp_sum += fac[k] * (exp(-(r-rr)**2 * facEx[k]) - exp(-(r+rr)**2 * facEx[k]))
                    tmp += val/rr * tmp_sum
                    rr += delta
        partCF[i,1] += tmp
    return partCF


# pddf.partCharFuncAdd() using Cython, significantly faster
@cython.cdivision(True)
@cython.boundscheck(False)
def partCharFuncAdd(np.ndarray[FTYPE_t, ndim=2] partCF, partDHisto, key, paramProd, rArray, double drPrime):
    """
    Adds contributions \f$ \int H(r') \delta(r-r') a_{i\nu}a_{j\mu} d r'\f$ to
    the inter-particle EPDDF.

    If (r=='r) then the corresponding value of the partial histgram weighted by
    the atom electron number square is added.

    @param partCF Partial EPDDF.
    @param partDHisto Partial distance histogram.
    @param key string Representing pair of particle species.
    @param paramProd Parameter dictionary for products of form factors.
    @param rArray Array of r-values at which characteristic function is evaluated.
    @param drPrime Interval size in r'. At r' the partial histtogram is evaluated.
    """
    param=paramProd[key]
    elements=key.split(",")
    #if elements[0]==elements[1]:
    NMean=partDHisto[key][0,1]
    #else:
    #    NMean=0.
    # print "NMean("+key+") =", NMean
    #partCF[0,1]+=NMean*param[0][0]
    #print "param[0][0]=", param[0][0]
    #exit(-1)
    cdef ITYPE_t i
    cdef ITYPE_t i_min = 1
    cdef ITYPE_t i_max = partCF.shape[0]
    cdef np.ndarray[FTYPE_t, ndim=2] partDHisto_key = np.asarray(partDHisto[key], dtype=FTYPE)
    cdef ITYPE_t j
    cdef ITYPE_t j_min = 1
    cdef ITYPE_t j_max = partDHisto_key.shape[0]
    cdef FTYPE_t tmp
    cdef FTYPE_t r
    cdef ITYPE_t r_i
    cdef FTYPE_t rPrime
    cdef ITYPE_t rPrime_i
    cdef FTYPE_t val
    cdef FTYPE_t par = param[0][0]
    for i in range(i_min, i_max):
        # r = round(partCF[i,0]*100000.0)
        r_i = lrint(partCF[i,0]*100000.0)
        tmp = 0.
        for j in range(j_min, j_max):
            # rPrime = round(partDHisto_key[j,0]*100000.0)
            rPrime_i = lrint(partDHisto_key[j,0]*100000.0)
            # if (r == rPrime): #DANGER
            if (r_i == rPrime_i): #DANGER
                val = partDHisto_key[j,1]
                # if (i % 100 == 0): print r, val*param[0][0]
                tmp += val*par/drPrime
                break
        partCF[i,1] += tmp
    return partCF
