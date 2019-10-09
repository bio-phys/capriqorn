#!/usr/bin/env python2
# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


# author: Juergen Koefinger
# input parameters:
#   number of elements
#   delta
#   PBCName: name of file containing names of "PBC_..." files produced by histograms
# output files:
#   (histo.dat: average distance histograms) has been commented out
#   rdf.PBC.dat: rdfs

from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import range
import numpy as np
import math
import sys
import rdf
from . import getRDFLib as getRDF

if len(sys.argv) == 3:
    PBCName = sys.argv[1]
    print()
    print(" PBCName =", PBCName)
    delta = float(sys.argv[2])
    print(" delta =", delta)
else:
    print(" Usage: " + sys.argv[0] + " PBCName delta \n")
    exit()


oname = PBCName.split('.')[0]
print(" oname = ", oname)

nameList = getRDF.readNameList(PBCName)
info = getRDF.getHistoInfo(nameList)

invVol = 0.
vol = 0.
qFirst = 0
norm = 0.
dt = np.dtype('d')
for i in range(len(info)):
    path = info[i]['name']
    print()
    print("", path)
    for line in info[i]['data']:
        name = path + "rdfHisto." + str(int(line[0])) + ".dat"
        invVol += line[3]
        vol += line[2]
        norm += line[1]
        print("", name)
        if qFirst == 0:
            histo = np.loadtxt(name, dtype=dt)
            qFirst = 1
        else:
            dummy = np.loadtxt(name, dtype=dt)
            histo[:, 1:] += dummy[:, 1:]
            # for i in range(len(histo)):
            #    for j in range(1,len(histo[i])):
            #        histo[i,j]+=dummy[i,j]
print()

header = rdf.readHeader(name)
print(header)

invVol /= norm
vol /= norm
# print
# print " average inverse volume =", invVol
for i in range(len(histo)):
    for j in range(1, len(histo[i])):
        histo[i, j] /= norm

#rdf.savetxtHeader('histo.dat', header, histo)

# print histo[1]
nProd = len(histo[1]) - 1
# print " nProd =", nProd
nElement = rdf.getNrElements(nProd)
# print " nElement =", nElement

temp = histo[0]
partNrs = []
counter = 1
for i in range(nElement):
    for j in range(i, nElement):
        if i == j:
            partNrs.append(temp[counter])
        counter += 1

# print " partNrs=", partNrs

partNrProd = []
fac = []
for i in range(nElement):
    for j in range(i, nElement):
        partNrProd.append(partNrs[i] * partNrs[j])
        if i == j:
            fac.append(1.)
        else:
            fac.append(2.)

# print " partNrProd=",  partNrProd

fourPi = 4. * math.pi
for i in range(1, len(histo)):
    rSqr = histo[i, 0] * histo[i, 0]
    for j in range(1, len(histo[i])):
        histo[i, j] /= (fourPi * rSqr * delta * invVol * partNrProd[j - 1] * fac[j - 1])

for j in range(1, len(histo[0])):
    histo[0, j] *= invVol

rdf.savetxtHeader("rdf." + oname + ".dat", header, histo)

print(" average inverse volume =", invVol)
print(" inverse average volume =", 1. / vol)
print(" ratio =", invVol * vol)
