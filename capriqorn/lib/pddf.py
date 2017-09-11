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
"""@package
    Library functions to calculate the pddf.
    Author: Juergen Koefinger
    The file <pddf.py> was created from the standalone script with the same
    name, any glue code outside of subroutines was stripped.  The implementation
    is done in <postproc_filter_pddf.py>.
"""


import os
import sys
import math
import numpy as np
import rdf
from . import formFactor as ff
import cadishi.util
# --- use fast Cython functions for time critical parts, if available
try:
    from capriqorn.kernel import c_pddf
    have_c_pddf = True
except:
    have_c_pddf = False
    print(" Note: capriqorn.lib.pddf: could not import c_pddf")


__author__ = "Juergen Koefinger"
__copyright__ = "Copyright (C) 2015 Juergen Koefinger"
__license__ = "license_tba"


def j0(x):
    """Spherical Bessel functions of the 1st kind for n=0,
    which is the sinc() function."""
    if x == 0:
        return 1.
    else:
        return math.sin(x) / x


def binning(data, n, dr, distQ=False):
    """Collect n adjacent bins in a single bin. The result is a histogram.
    The x-value of the new bin is given by the average of the n x-values.
    Add a line to data at the beginning, which contains differences in
    particle numbers, and set x-value to zero.
    """
    tmp = data[0, :].copy()
    data[0, :] = 0
    new = np.zeros((len(data) / n + 1, len(data[0])))
    if distQ:
        fac = 1. / float(n)
        iadd = 1
    else:
        fac = 1.
        iadd = 0
    for i in range(len(data) / n):
        total = np.zeros(len(data[0]))
        for j in range(n):
            total[:] += data[i * n + j + iadd, :]
        # average/=float(n) #DANGER
        new[i + 1, 1:] = total[1:] * fac
        new[i + 1, 0] = total[0] / float(n)
    new[0, :] = tmp[:]
    new[0, 0] = 0
    return new, dr * n


def coarsen_histogram(data, n, dr, distQ=False):
    """Re-implementation of the `binning()` routine,
    compatible w/ capriqorn data structures.
    """
    data_new = {}
    if distQ:
        fac = 1. / float(n)
        iadd = 1
    else:
        fac = 1.
        iadd = 0
    # --- coarsen data
    radii = data['radii']
    radii_new = []  # Python list, to be converted to NumPy below
    count = 0
    r_avg = 0.0
    for rad in radii:
        count += 1
        r_avg += rad
        if (count % n == 0):
            radii_new.append(r_avg / float(n))
            r_avg = 0.0
    if (count % n > 0):
        # remainder
        radii_new.append(r_avg / float(count % n))
    data_new['radii'] = np.array(radii_new)
    # --- coarsen data
    for key in data:
        if (key == 'radii'):
            continue
        histo_new = []  # Python list, to be converted to NumPy below
        count = 0
        bin_new = 0
        for bin_old in data[key]:
            count += 1
            bin_new += bin_old
            if (count % n == 0):
                histo_new.append(fac * bin_new)
                bin_new = 0
        if (count % n > 0):
            histo_new.append(fac * bin_new)
        data_new[key] = np.array(histo_new)
        # --- first line special entry
        (data_new[key])[0] = (data[key])[0]
    # ---  first line special entry
    (data_new['radii'])[0] = 0.0
    return data_new, dr * n


def getPartCharFunc1_Python(partDHisto, key, paramProd, rArray, drPrime, delta):
    """Calculates intra-atom contributions.
    """
    partCF = np.zeros((len(rArray), 2))
    partCF[:, 0] = rArray[:]
    param = paramProd[key]
    elements = key.split(",")
    NMean = partDHisto[key][0, 1]
    # print "NMean("+key+") =", NMean
    partCF[0, 1] += NMean * param[0][0]
    # print "param[0][0]=", param[0][0]
    dr = drPrime  # DANGER
    for i, [r, valCF] in enumerate(partCF[1:]):
        # if (i % 100 == 0): print " r =", r
        rSqr = r * r
        # DANGER
        tmp = 0.
        # for rr in np.arange(r-0.5*(dr-delta), r+0.5*dr, delta):
        #    rrSqr=rr*rr
        #    tmp+=ff.FT1(param, rrSqr)*delta/dr
        tmp = ff.FT1(param, rSqr)
        partCF[i + 1, 1] += NMean * tmp
    return partCF


def getPartCharFunc1(partDHisto, key, paramProd, rArray, drPrime, delta):
    """Calculates intra-atom contributions.
    """
    if have_c_pddf:
        return c_pddf.getPartCharFunc1(partDHisto, key, paramProd, rArray, drPrime, delta)
    else:
        return getPartCharFunc1_Python(partDHisto, key, paramProd, rArray, drPrime, delta)


def getPartCharFunc2Org(partDHisto, key, paramProd, rArray, drPrime, delta):
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
    partCF = np.zeros((len(rArray), 2))
    partCF[:, 0] = rArray[:]
    param = paramProd[key]
    elements = key.split(",")
    NMean = partDHisto[key][0, 1]
    print "NMean(" + key + ") =", NMean

    a = np.asarray(param[0][1:])
    b = np.asarray(param[1][1:])
    dr = drPrime  # DANGER
    for i, [r, valCF] in enumerate(partCF[1:]):
        if (i % 100 == 0):
            print " r =", r
        tmp = 0.
        for [rPrime, val] in partDHisto[key][1:]:
            if val != 0:
                for rr in np.arange(rPrime - 0.5 * (drPrime - delta), rPrime + 0.5 * drPrime, delta):
                    tmp += val * r / rr * ff.FT2(a, b, r, rr) * delta / drPrime
        partCF[i + 1, 1] += tmp
    return partCF


# @do_profile(follow=[])
def getPartCharFunc2_Python(partDHisto, key, paramProd, rArray, drPrime, delta):
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
    partCF = np.zeros((len(rArray), 2))
    partCF[:, 0] = rArray[:]
    param = paramProd[key]
    elements = key.split(",")
    NMean = partDHisto[key][0, 1]
    # print "NMean("+key+") =", NMean
    a = np.asarray(param[0][1:])
    b = np.asarray(param[1][1:])
    fac = a / (2. * np.sqrt(b * np.pi))
    facEx = 1. / (4. * b)
    dr = drPrime  # DANGER
    for i, [r, valCF] in enumerate(partCF[1:]):
        # if (i % 100 == 0): print " r =", r
        tmp = 0.
        for [rPrime, val] in partDHisto[key][1:]:
            if (rPrime - r) ** 2 < 9:  # MODI
                if val != 0:
                    val *= r * delta / drPrime
                    for rr in np.arange(rPrime - 0.5 * (drPrime - delta), rPrime + 0.5 * drPrime, delta):
                        tmp += val / rr * (fac * (np.exp(-(r - rr) ** 2 * facEx) -
                                                  np.exp(-(r + rr) ** 2 * facEx))).sum()
        partCF[i + 1, 1] += tmp
    return partCF


def getPartCharFunc2(partDHisto, key, paramProd, rArray, drPrime, delta):
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
    if have_c_pddf:
        return c_pddf.getPartCharFunc2(partDHisto, key, paramProd, rArray, drPrime, delta)
    else:
        return getPartCharFunc2_Python(partDHisto, key, paramProd, rArray, drPrime, delta)


# --- original function before any Cython work
# def getPartCharFunc2(partDHisto, key, paramProd, rArray, drPrime, delta):
#     """
#     Calculates inter-atom contributions to the EPDDF for a partial distance histogram.
#
#     @param partDHisto Partial distance histogram.
#     @param key string Representing pair of particle species.
#     @param paramProd Parameter dictionary for products of form factors.
#     @param rArray Array of r-values at which characteristic function is evaluated.
#     @param drPrime Interval size in r'. At r' the partial histtogram is evaluated.
#     @param delta Interval size for integration in r'. The \f$c_{ij}(r,r')\f$ are
#                  evaluated within the bin at r' at sub-intevals delta.
#     """
#     partCF=np.zeros((len(rArray), 2))
#     partCF[:,0]=rArray[:]
#     param=paramProd[key]
#     elements=key.split(",")
#     NMean=partDHisto[key][0,1]
#     print "NMean("+key+") =", NMean
#
#     a=np.asarray(param[0][1:])
#     b=np.asarray(param[1][1:])
#     fac=a/(2.*np.sqrt(b*np.pi))
#     facEx=1./(4.*b)
#     dr=drPrime #DANGER
#     for i, [r, valCF] in enumerate(partCF[1:]):
#         if (i % 100 == 0): print " r =", r
#         tmp=0.
#         for [rPrime, val] in partDHisto[key][1:]:
#             if (rPrime-r)**2<9: #MODI
#                 if val!=0:
#                     val*=r*delta/drPrime
#                     for rr in np.arange(rPrime-0.5*(drPrime-delta), rPrime+0.5*drPrime, delta):
#                         tmp+=val/rr*(fac*(np.exp(-(r-rr)**2*facEx)-np.exp(-(r+rr)**2*facEx))).sum()
#         partCF[i+1,1]+=tmp
#     return partCF


def partCharFuncAdd_Python(partCF, partDHisto, key, paramProd, rArray, drPrime):
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
    param = paramProd[key]
    elements = key.split(",")
    # if elements[0]==elements[1]:
    NMean = partDHisto[key][0, 1]
    # else:
    #    NMean=0.
    # print "NMean("+key+") =", NMean
    # partCF[0,1]+=NMean*param[0][0]
    # print "param[0][0]=", param[0][0]
    # exit(-1)
    for i, [r, valCF] in enumerate(partCF[1:]):
        tmp = 0.
        for [rPrime, val] in partDHisto[key][1:]:
            # print rPrime, val
            # if val!=0:
            if (round(r * 100000) == round(rPrime * 100000)):  # DANGER
                # if (i % 100 == 0): print r, val*param[0][0]
                tmp += val * param[0][0] / drPrime
                break
        partCF[i + 1, 1] += tmp
    return partCF


def partCharFuncAdd(partCF, partDHisto, key, paramProd, rArray, drPrime):
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
    if have_c_pddf:
        return c_pddf.partCharFuncAdd(partCF, partDHisto, key, paramProd, rArray, drPrime)
    else:
        return partCharFuncAdd_Python(partCF, partDHisto, key, paramProd, rArray, drPrime)


# --- original function before any Cython work
# def partCharFuncAdd(partCF, partDHisto, key, paramProd, rArray, drPrime):
#     """
#     Adds contributions \f$ \int H(r') \delta(r-r') a_{i\nu}a_{j\mu} d r'\f$ to
#     the inter-particle EPDDF.
#
#     If (r=='r) then the corresponding value of the partial histgram weighted by
#     the atom electron number square is added.
#
#     @param partCF Partial EPDDF.
#     @param partDHisto Partial distance histogram.
#     @param key string Representing pair of particle species.
#     @param paramProd Parameter dictionary for products of form factors.
#     @param rArray Array of r-values at which characteristic function is evaluated.
#     @param drPrime Interval size in r'. At r' the partial histtogram is evaluated.
#     """
#     param=paramProd[key]
#     elements=key.split(",")
#     #if elements[0]==elements[1]:
#     NMean=partDHisto[key][0,1]
#     #else:
#     #    NMean=0.
#     print "NMean("+key+") =", NMean
#
#     #partCF[0,1]+=NMean*param[0][0]
#     #print "param[0][0]=", param[0][0]
#     #exit(-1)
#     for i, [r, valCF] in enumerate(partCF[1:]):
#         tmp=0.
#         for [rPrime, val] in partDHisto[key][1:]:
#             #print rPrime, val
#             #if val!=0:
#             if (round(r*100000) == round(rPrime*100000)): #DANGER
#                 if (i % 100 == 0): print r, val*param[0][0]
#                 tmp+=val*param[0][0]/drPrime
#                 break
#         partCF[i+1,1]+=tmp
#     return partCF


def FTCharFunc(partCFArray, dr, qList):
    """
    Fourier transform of the characteristic function.

    @param partCFArray Partial EPDDFs.
    @param dr Distance interval size of the partial EPDDFs.
    @param qList List of q-values.
    """
    intensity = np.zeros((len(qList), 2))
    partInt = np.zeros((len(qList), len(partCFArray[0])))
    intensity[:, 0] = qList[:]
    partInt[:, 0] = qList[:]
    for j, q in enumerate(qList):
        for i, r in enumerate(partCFArray[:, 0]):
            sinc = j0(q * r)
            for k in range(1, len(partCFArray[i])):
                if r > 0:
                    partInt[j, k] += partCFArray[i, k] * sinc * dr
                else:
                    partInt[j, k] += partCFArray[i, k] * sinc
    # partInt[:,1:]*=dr
    for j, q in enumerate(intensity[:, 0]):
        intensity[j, 1] = partInt[j, 1:].sum()
    return intensity, partInt


def bulkSolvHistogram(g, dr):
    """
    Generate partial pair-distance histograms of bulk solvent from partial radial distribution functions.
    """
    nProd = len(g[0, 1:])
    nrEl = rdf.getNrElements(nProd)
    elCol = rdf.getElementColumns(nrEl)
    indexPairs = rdf.getIndexPairs(nrEl)
    print " indexPairs =", indexPairs
    elPairs = rdf.getElementPairs(indexPairs, elCol)
    print " elPairs =", elPairs
    tmp = 4. * math.pi * g[1:, 0] * g[1:, 0] * dr
    for i in range(1, nProd + 1):
        print indexPairs[i]
        i0 = elPairs[i][0]
        i1 = elPairs[i][1]
        rhoProd = g[0, i0] * g[0, i1]
        # print i0, i1, rhoProd, g[0,i0], g[0, i1]
        g[1:, i] = rhoProd * tmp * (g[1:, i] - g[-1, i])
    return g


def bulkSolvHistogram_dict(g, dr):
    """Generate partial pair-distance histograms of bulk solvent from partial radial distribution functions.
    Dictionary-based re-implementation of bulkSolvHistogram(g, dr), to be compatible with Capriqorn.
    """
    tmp = 4. * math.pi * g['radii'][1:] * g['radii'][1:] * dr
    for key in g:
        if (key == 'radii'):
            continue
        (el1, el2) = key.split(',')
        rhoProd = g[el1 + ',' + el1][0] * g[el2 + ',' + el2][0]
        g[key][1:] = rhoProd * tmp * (g[key][1:] - g[key][-1])
    return g
