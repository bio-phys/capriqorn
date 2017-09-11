# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

"""Form factor routines
"""

import math
import copy
import numpy as np
import six


def readAtomSFParam(filename):
    # example of two entries in an atom structure factor file

    # H
    #     1         1        0.003038
    #    0.493002        0.322912        0.140191        0.040810
    #   10.510900       26.125700        3.142360       57.799698
    #    0.000000        0.000000        0.000000        0.000000
    # C
    #     6         6        0.215600
    #    2.310000        1.020000        1.588600        0.865000
    #   20.843899       10.207500        0.568700       51.651199
    #    0.017000        0.009000        0.002000        0.002000

    formfactor = dict()
    atomname = None
    with open(filename) as fp:
        for i, line in enumerate(fp):
            line = line.strip().split()
            # first read name of atom type
            if i % 5 == 0:
                if len(line) != 1:
                    raise RuntimeError("Expected atomname in atomfs")
                atomname = line[0]
                formfactor[atomname] = []
            # all remaining lines are added to that atomname
            else:
                if atomname is None:
                    raise RuntimeError("Wrong atom fs file format")
                formfactor[atomname].append([float(num) for num in line])
    return formfactor


def writeAtomSFParam(ffDict, fn):
    with open(fn, 'w') as fp:
        for atom, form_factor in six.iteritems(ffDict):
            if len(form_factor) != 4:
                raise RuntimeError("Wrong structure form factor dict")
            fp.write('{}\n'.format(atom))
            for factors in form_factor:
                fp.write("       ")
                for num in factors:
                    fp.write(" {:8.6f}".format(num))
                fp.write("\n")


def reformatSFParam(param):
    """
    In this parameter format, the constant c is given by a Gaussian a*exp(-b*q^2) with b=0
    The factor 1/(4 Pi)^2 is absorbed in b.
    """
    newParam = {}
    fourPi = 4. * math.pi
    fac = 1. / (fourPi * fourPi)
    for k in param.keys():
        newParam[k] = [np.asarray(
            [param[k][0][2]] + param[k][1]), np.asarray([0.] + param[k][2]) * fac]
    return newParam


def SFParamProd(newParam):
    """ newParam is a dictionary """
    paramProd = {}
    # print newParam.keys()
    for k1 in newParam.keys():
        for k2 in newParam.keys():
            k = k1 + "," + k2
            # paramProd[k]=[np.asarray(newParam[k1][0])*np.asarray(newParam[k1][0]), newParam[k1][1]+newParam[k1][1]]
            l1 = []
            l2 = []
            for i in range(len(newParam[k1][0])):
                for j in range(len(newParam[k2][0])):
                    fac = 1.
                # for j in range(i, len(newParam[k2][0])):
                #    if (i==j):
                #        fac=1.
                #    else:
                #        fac=2.
                    l1.append(fac * newParam[k1][0][i] * newParam[k2][0][j])
                    l2.append(newParam[k1][1][i] + newParam[k2][1][j])
            paramProd[k] = copy.copy([l1, l2])
    return paramProd

# NOTE: reimplementation in kernel/c_pddf.pyx


def FT1Func(a, b, rSqr):
    """
    Calculate: 2/pi Int[ f^2(q) sin(qr) (qr) dq = a r^2/(2 sqrt(pi b^3)) exp(-r^2/(4b))
    """
    if b > 0:
        return a * rSqr / (2. * math.sqrt(math.pi * b * b * b)) * math.exp(-rSqr / (4. * b))
    else:
        # if rSqr==0:
        #    return a
        # else:
        #    return 0.
        return 0.

# NOTE:  reimplementation in kernel/c_pddf.pyx


def FT1(paramList, rSqr):
    """ paramList
    """
    val = 0.
    for i in range(len(paramList[0])):
        tmp = FT1Func(paramList[0][i], paramList[1][i], rSqr)
        val += tmp
    return val


def printFT1(paramList, rList):
    for r in rList:
        rSqr = r * r
        print r, FT1(paramList, rSqr)
    return


def FT2Func(a, b, rMinusSqr, rPlusSqr):
    if b > 0:
        return a / (2. * math.sqrt(b * math.pi)) * (math.exp(-rMinusSqr / (4. * b)) - math.exp(-rPlusSqr / (4. * b)))
    else:
        # if rMinusSqr==0:
        #    return a
        # else:
        #    return 0.
        return 0.


def FT2(a, b, r, rPrime):
    """ a and b are numpy arrays """
    rMinusSqr = (r - rPrime) * (r - rPrime)
    rPlusSqr = (r + rPrime) * (r + rPrime)
    return (a / (2. * np.sqrt(b * np.pi)) * (np.exp(-rMinusSqr / (4. * b)) - np.exp(-rPlusSqr / (4. * b)))).sum()


def fiveGaussian(param, q):
    """ param is a list """
    val = 0.
    qSqr = q * q
    fourPi = 4. * math.pi
    fac = 1. / (fourPi * fourPi)
    for i in range(len(param[1])):
        val += param[1][i] * math.exp(-qSqr * param[2][i] * fac)
    val += param[0][2]
    return val


def printFiveGaussian(param, qList):
    for q in qList:
        print q, fiveGaussian(param, q)
    return
