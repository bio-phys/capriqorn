# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""RDF calculation.
"""


import numpy as np
import math


def ASph(qR):
    if(qR == 0):
        return 1.
    else:
        return 3. * (math.sin(qR) - qR * math.cos(qR)) / (qR * qR * qR)


def ISph(qR):
    if(qR == 0):
        return 1.
    else:
        return 9. * math.pow(math.sin(qR) - qR * math.cos(qR), 2) / math.pow(qR, 6)


def getNrElements(nProd):
    return int(-0.5 + math.sqrt(0.25 + 2. * nProd))


def readHeader(filename):
    with open(filename) as fp:
        return fp.readline()


def savetxtHeader(name, header, array, fmt="%le"):
    """
    Save data including header.
    """
    with open(name, 'w') as fp:
        fp.write(header)
        np.savetxt(fp, array, fmt=fmt)


def SSphere(r):
    """
    Surface of a sphere of radius r.
    """
    return 4. * math.pi * r * r


def Ar(h, r):
    """
    Surface area of a spherical cap of height 'h'.
    """
    return 2. * math.pi * r * h


def HDelta(x, R, r):
    """
    Height of spherical cap of formed a sphere of radius r by the intersection of two spheres of radii r and R at a distance x.
    Eq. (A3) of Phys. Rev. E vol. 87 p. 052712 (2013)
    """
    if x * x <= (R * R - r * r):
        return ((x + r) * (x + r) - R * R) / (2. * x)
    else:
        return -((x - r) * (x - r) - R * R) / (2. * x)


def HDeltaFast(xvec, R, r):
    """
    Height of spherical cap of formed a sphere of radius r by the intersection of two spheres of radii r and R at a distance x.
    Eq. (A3) of Phys. Rev. E vol. 87 p. 052712 (2013)
    Vectorized implementation.
    """
    val = xvec.copy()
    indices = (xvec ** 2 < (R ** 2 - r ** 2))
    val[indices] = ((xvec[indices] + r) ** 2 - R ** 2) / (2. * xvec[indices])
    val[~indices] = -((xvec[~indices] - r) ** 2 - R ** 2) / (2. * xvec[~indices])
    return val


def Sr(x, R, r):
    """
    Surface area of a sphere of radius r at a distance x from the center of sphere of radius R that lies outside the R-sphere.
    Eqs. (A1) and (A2) of Phys. Rev. E vol. 87 p. 052712 (2013)
    """
    val = 0
    if x * x + r * r <= R * R:
        if x <= R - r:
            val = SSphere(r)
        else:
            val = SSphere(r) - Ar(HDelta(x, R, r), r)
    elif R + r <= x or x <= r - R:
        val = 0
    else:
        val = Ar(HDelta(x, R, r), r)
    return val


def SrFast(xvec, R, r):
    """
    Surface area of a sphere of radius r at a distance x from the center of sphere of radius R that lies outside the R-sphere.
    Eqs. (A1) and (A2) of Phys. Rev. E vol. 87 p. 052712 (2013)
    Vectorized implementation.
    """
    val = np.zeros(xvec.shape[0])
    mask1 = (xvec ** 2 + r ** 2 <= R ** 2)

    mask2 = (xvec <= R - r)
    mask11 = np.logical_and(mask1, mask2)
    mask12 = np.logical_and(mask1, ~mask2)
    val[mask11] = SSphere(r)
    val[mask12] = SSphere(r) - Ar(HDeltaFast(xvec[mask12], R, r), r)

    mask3 = np.logical_and(~np.logical_or(
        xvec >= R + r, xvec <= r - R), ~mask1)
    val[mask3] = Ar(HDeltaFast(xvec[mask3], R, r), r)
    return val


def pRg(r, Rg):
    return 3. * math.exp(-3. * r * r / (4. * Rg * Rg)) * math.sqrt(3. / math.pi) * r * r / (2. * Rg * Rg * Rg)


def P(r, R):
    """
    Normalized pair distance distribution function of a structureless sphere.
    Eq. (A4) of Phys. Rev. E vol. 87 p. 052712 (2013)
    """
    if r >= 0 and r <= 2 * R:
        return 3. * math.pow(r, 5) / (16. * math.pow(R, 6)) - 9. * math.pow(r, 3) / (4 * math.pow(R, 4)) + 3 * math.pow(r, 2) / math.pow(R, 3)
    else:
        return 0.


def PInt(r, R):
    return math.pow(r, 6) / (32. * math.pow(R, 6)) - 9. * math.pow(r, 4) / (16. * math.pow(R, 4)) + math.pow(r, 3) / math.pow(R, 3)


def getRDF(data, R, col, delta):
    norm = np.sum(data[:, col]) - data[0, col]
    nr = data[0, col]
    print norm, nr, norm / nr ** 2
    res = np.zeros((len(data[:, col]), 2))
    print len(data[:, col])
    for i in range(1, len(data[:, col])):
        res[i, 0] = data[i, 0]
        res[i, 1] = data[i, col] / (P(res[i, 0], R) * nr * nr * delta)
    return res


def VSphere(R):
    """
    Volume of a sphere or radius R.
    """
    return 4. * math.pi * R * R * R / 3.


def VShell(R1, R2):
    """
    Volume of a spherical shell with inner radius radius R1 and outer radius R2.
    """
    return VSphere(R2) - VSphere(R1)


def m(R, r):
    if r >= 0 and r <= 2 * R:
        return 1. / 3. * math.pi * math.pi * r * r * (r - 2. * R) * (r - 2. * R) * (r + 4. * R)
    else:
        return 0.


def m1(R1, R2, r):
    if r >= 0 and r < R2 - R1:
        return 4. / 3. * math.pi * r * r * R1 * R1 * R1
    else:
        return 0.


def m2(R1, R2, r):
    if r >= R2 - R1 and r <= R1 + R2:
        return 1. / 12. * math.pi * r * (R1 + R2 - r) * (R1 + R2 - r) * (r * r - 3 * (R1 - R2) * (R1 - R2) + 2 * r * (R1 + R2))
    else:
        return 0.


def mSum(R1, R2, r):
    return 4. * math.pi * (m1(R1, R2, r) + m2(R1, R2, r))


def MSh(R1, R2, r):
    """
    Pair distance distribution function of spherical shell with inner radius R1 an outer radius R2.
    """
    if r >= 0 and r <= 2. * R2:
        return m(R2, r) + m(R1, r) - 8. * math.pi * (m1(R1, R2, r) + m2(R1, R2, r))
    else:
        return 0.


def M1Sh(R1, R2, r):
    if r >= 0 and r <= (R1 + R2):
        return 8. * math.pi * (m1(R1, R2, r) + m2(R1, R2, r)) - 2. * m(R1, r)
    else:
        return 0.


def M(R1, R2, r):
    if r >= 0 and r <= (R1 + R2):
        return 8. * math.pi * (m1(R1, R2, r) + m2(R1, R2, r)) - m(R1, r)
    else:
        return 0.


def getMNorm(R1, R2, g, rho, dr):
    """
    Calculate norm of distance distribution function of spherical core region and surrounding spherical shell.
    (structured liquid with radial distribution function "g")
    """
    norm = 0.
    for r, val in g:
        norm += M(R1, R2, r) * val
    norm *= rho * rho * dr
    return norm


def PSh(R1, R2, r):
    """
    Normalized pair-distance distribution function of spherical shell with inner radius R1 an outer radius R2.
    """
    return MSh(R1, R2, r) / VShell(R1, R2) ** 2

# def getRDFInhom(distData, lenData, R, col, delta, lenCol):
#    norm=np.sum(distData[:,col])-distData[0,col]
#    nr=distData[0,col]
#    rho=nr/VSphere(R)
#    print norm, nr, norm/nr**2
#    res=np.zeros( (len(distData[:,col]),2))
#    print len(distData[:,col])
#    for i in range(1, len(distData[:,col])) :
#        r=distData[i,0]
#        res[i,0]=r
#        integral=0.
#        for j in range(len(lenData[:,lenCol])):
#            x=lenData[j,0]
#            integral+=lenData[j,lenCol]*Sr(x, R, r)
#        res[i,1]=distData[i,col]/(integral*rho*delta)
#    return res
#
# def renormRDFSphere(distData, res, frac, R, delta, col):
#    norm=0.
#    for i in range(1,len(distData)):
#    #    r=distData[i,0]
#    #    if r<frac*R:
#        norm+=distData[i,col]
#    print " norm =", norm
#
#    resnorm=0.
#    for i in range(1,len(res)):
#        r=res[i,0]
#        if r<frac*R:
#            #resnorm+=res[i,1]*(PInt(r+delta/2, R)-PInt(r-delta/2, R))/delta
#            resnorm+=res[i,1]*P(r, R)
#    resnorm*=delta
#    print " resnorm =", resnorm
#
#    nr=distData[0,col]
#    print " nr =", nr
#    print " norm/nr**2 =", norm/nr**2
#    fac=norm/nr**2*PInt(frac*R, R)
#    print " fac =", fac
#    print " fac/resnorm =", fac/resnorm
#    for i in range(1,len(res)-1):
#        res[i,1]*=fac/resnorm
#
#    resnorm=0.
#    for i in range(1,len(res)-1):
#        resnorm+=res[i,1]
#    resnorm*=delta
#    print " resnorm =", resnorm
#    return res


def getElementColumns(nrElements):
    elementColumns = [0, 1]
    for i in range(nrElements - 1):
        elementColumns.append(elementColumns[-1] + nrElements - i)
    return elementColumns


def getIndexPairs(nrElements):
    counter = 1
    indexPairs = [[]]
    for i in range(1, nrElements + 1):
        for j in range(i, nrElements + 1):
            counter += 1
            indexPairs.append([i, j])
            # print counter, i, j
    return indexPairs


def getElementPairs(indexPairs, elementColumns):
    elementPairs = [[]]
    for i in range(1, len(indexPairs)):
        i0 = indexPairs[i][0]
        i1 = indexPairs[i][1]
        elementPairs.append([elementColumns[i0], elementColumns[i1]])
        # print i, indexPairs[i]
    # print elementPairs
    return elementPairs


def getElementPairsAtOnce(histo):
    nProd = len(histo[0, 1:])
    nrEl = getNrElements(nProd)
    elCol = getElementColumns(nrEl)
    indexPairs = getIndexPairs(nrEl)
    elPairs = getElementPairs(indexPairs, elCol)
    return elPairs, nrEl, elCol


def fade(xval, yval, ginfty, l):
    """
    Decrease noise in plateau of rdf.

    Parameters
    ----------
    xval: array_like
    yval: array_like
    l: float
        Decay constant for exponetial tapering.
    ginfty: float
        Limiting value of rdf.
    Returns
    -------
    newVal: array_like
        New rdf values with tapered noise.
    """
    temp = (xval) / l
    temp *= temp
    newVal = ginfty + (yval - ginfty) * math.exp(-temp)
    return newVal


def getRDFCumu(histo, delta):
    """
    Returns
    -------
    histoCumu: array_like
        Integrated rdfs from large to small distances.
    """
    # Leave out last bin, which later is set to ginfty. Thus, reapplying this function won't change ginfty.
    histoCumu = histo[:-2, :].copy()
    for j in range(1, len(histoCumu[-1])):
        histoCumu[-1, j] *= delta

    for i in range(len(histo[:-2, :]) - 2, 1, -1):
        for j in range(1, len(histo[i])):
            histoCumu[i, j] *= delta
            histoCumu[i, j] += histoCumu[i + 1, j]

    for j in range(1, len(histoCumu[0])):
        histoCumu[0, j] = 0.
    return histoCumu


def getStartingBin(histo, fitFraction):
    """
    Returns
    -------
    index: int
        Index of bin at approximately 'fitFraction'*(maximal distance) from the end.
    """
    index = len(histo) - int(len(histo) * fitFraction)
    return index


def getPlateauValue(histoCumu, index):
    """
    Estimates plateau values by fitting linear function to integral of rdfs (integrated started from maximum distance).
    """
    ginfty = []
    for j in range(1, len(histoCumu[0])):
        par = np.polyfit(histoCumu[index:-1, 0], histoCumu[index:-1, j], 1)
        ginfty.append(-par[0])
    return ginfty


def taperNoise(histo, index, ginfty, noiseFraction=0.01, verb=False):
    """
    Tapers noise by subtracting ginfty from rdf, multiplying the resulting residuals with rapidly decaying function, and adding back ginfty.
    If noiseFraction is set to 1 then no tapering of the noise takes place.
    """
    histo_out = histo.copy()
    if 0 < noiseFraction and noiseFraction < 1:
        dR = histo[-1, 0] - histo[index, 0]
        l = math.sqrt(-dR**2 / math.log(noiseFraction))
        rStart = histo[index, 0]
        if verb == True:
            print " Smoothening rdfs from bin", index, "at distance r =", rStart, "to bin", len(histo), "at distance r =", histo[-1, 0], ".\n"
        for i in range(index, len(histo)):
            r = math.sqrt(histo[i, 0] * histo[i, 0])
            for j in range(1, len(histo[i])):
                histo_out[i, j] = fade((r - rStart), histo[i, j], ginfty[j - 1], l)
    return histo_out


def setGinfty(histo, ginfty):
    for j in range(1, len(histo[-1])):
        histo[-1, j] = ginfty[j - 1]
    return histo


def smooth(histo, delta, fitFraction,  noiseFraction, verb=False):
    """
    Tapering noise in rdfs.

    Notes
    -----
    The parameter 'fitFraction' is the fraction of the rdf distance range at its end, where the rdf shows a plateau.
    'fitFraction' should not be larger than the shortest plateau of the partial rdfs.
    """
    histoCumu = getRDFCumu(histo, delta)
    index = getStartingBin(histo, fitFraction)
    ginfty = getPlateauValue(histoCumu, index)
    index = getStartingBin(histo, fitFraction)
    histo_smooth = taperNoise(histo, index, ginfty, noiseFraction, verb=verb)
    histo_smooth = setGinfty(histo_smooth, ginfty)
    return histo_smooth
