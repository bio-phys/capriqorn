# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Intensity calculation from histograms.
"""
from __future__ import division


from builtins import range
from past.utils import old_div
import numpy as np
import math
from six.moves import range

from . import formFactor as ff


def intensitiesFFFaster(nq, dq, dIntegrand, keys, ffDict, dr):
    """ uses atomistic form factors """
    dIntensity = np.zeros((nq, 2), dtype=float)
    partInt = np.zeros((nq, len(dIntegrand[0])))
    nameList = [k.split(",") for k in keys]
    # print "nameList=",nameList
    qList = np.zeros(nq)
    qList[:] = [float(i * dq) for i in range(nq)]
    dIntensity[:, 0] = qList[:]
    partInt[:, 0] = qList[:]
    rList = dIntegrand[:, 0]
    # for j in range(0,len(dIntegrand)):
    #    r=dIntegrand[j,0]
    #    sinc=j0(q*r)
    formFacProd = np.zeros((nq, len(dIntegrand[0])))
    for i in range(nq):
        sincList = np.sinc(old_div(rList * qList[i], math.pi)) * dr
        for k in range(1, len(dIntegrand[0])):
            # print k
            formFacProd[i, k] = ff.fiveGaussian(ffDict[nameList[k - 1][0]], qList[i])\
                * ff.fiveGaussian(ffDict[nameList[k - 1][1]], qList[i])
            partInt[i, k] += (sincList[:] * dIntegrand[:, k]
                              ).sum() * formFacProd[i, k]
    for i in range(nq):
        dIntensity[i, 1] = partInt[i, 1:].sum()
    return partInt, dIntensity


def getPartNrsProd(partNrs):
    partNrsProd = np.zeros(old_div(len(partNrs) * (len(partNrs) + 1), 2))
    k = 0
    for i in range(len(partNrs)):
        for j in range(i, len(partNrs)):
            partNrsProd[k] = partNrs[i] * partNrs[j]
            k += 1
    return partNrsProd


def getBulkIntegrand(rdf, densities):
    dH = rdf.copy()
    tmp = dH[-1, 1:]
    dH[:, 1:] -= tmp[np.newaxis, :]
    tmp = 4. * np.pi * dH[:, 0] ** 2
    dH[:, 1:] *= tmp[:, np.newaxis]
    rhoProd = getPartNrsProd(densities)
    dH[:, 1:] *= rhoProd[np.newaxis, :]
    return dH


def intensitiesFFIntraAtom(nq, dq, partNrs, nameList, ffDict):
    """ uses atomistic form factors """
    dIntensity = np.zeros((nq, 2), dtype=float)
    partInt = np.zeros((nq, len(partNrs) + 1))
    qList = np.zeros(nq)
    qList[:] = [float(i * dq) for i in range(nq)]
    dIntensity[:, 0] = qList[:]
    partInt[:, 0] = qList[:]
    # for j in range(0,len(dIntegrand)):
    #    r=dIntegrand[j,0]
    #    sinc=j0(q*r)
    k = 0
    formFacProd = np.zeros((nq, len(partNrs) + 1))
    # partNrsProd=getPartNrsProd(partNrs)
    # print "partNrsProd ", partNrsProd
    for i in range(nq):
        for k in range(1, len(partNrs) + 1):
            # print k
            formFacProd[i, k] = ff.fiveGaussian(
                ffDict[nameList[k - 1]], qList[i]) ** 2
            partInt[i, k] += partNrs[k - 1] * formFacProd[i, k]
    for i in range(nq):
        dIntensity[i, 1] = partInt[i, 1:].sum()
    return partInt, dIntensity
