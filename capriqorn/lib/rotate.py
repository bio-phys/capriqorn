# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Rotate coordinate sets using Euler angles.
"""
from __future__ import division
from __future__ import print_function


from past.utils import old_div
import numpy as np


def getAngles(vec):
    r = np.sqrt((vec ** 2).sum())
    if (r == 0):
        print("r=0")
    if (vec[0] == 0):
        print("x=0")
    phi = np.arctan2(vec[1], vec[0])
    theta = np.arccos(old_div(vec[2], r))
    return phi, theta


def getCoordinates(r, theta, phi):
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return np.array([x, y, z])


def getRx(phi):
    R = np.zeros((3, 3))
    R[0, 0] = 1
    R[1, 1] = np.cos(phi)
    R[1, 2] = -np.sin(phi)
    R[2, 1] = np.sin(phi)
    R[2, 2] = np.cos(phi)
    return R


def getRy(phi):
    R = np.zeros((3, 3))
    R[0, 0] = np.cos(phi)
    R[0, 2] = np.sin(phi)
    R[1, 1] = 1
    R[2, 0] = -np.sin(phi)
    R[2, 2] = np.cos(phi)
    return R


def getRz(phi):
    R = np.zeros((3, 3))
    R[0, 0] = np.cos(phi)
    R[0, 1] = -np.sin(phi)
    R[1, 0] = np.sin(phi)
    R[1, 1] = np.cos(phi)
    R[2, 2] = 1.
    return R


def getD(phi):
    R = np.zeros((3, 3))
    R[0, 0] = np.cos(phi)
    R[0, 1] = np.sin(phi)
    R[1, 0] = -np.sin(phi)
    R[1, 1] = np.cos(phi)
    R[2, 2] = 1.
    return R


def getC(phi):
    R = np.zeros((3, 3))
    R[0, 0] = 1.
    R[1, 1] = np.cos(phi)
    R[1, 2] = np.sin(phi)
    R[2, 1] = -np.sin(phi)
    R[2, 2] = np.cos(phi)
    return R


def rotate(coor, alpha, beta, gamma):
    """Rotate 'coor' by the angles alpha, beta, gamma.
    """
    R1 = getD(alpha)
    R2 = getC(beta)
    R3 = getD(gamma)
    M = R3 * R2 * R1
    return np.dot(coor, M)


# def rotate(coor, alpha, beta, gamma):
#     newCoor = coor.copy()
#     # n2 = coor.copy()
#     # R1=getRz(alpha)
#     # R2=getRy(beta)
#     # R3=getRz(gamma)
#     R1 = getD(alpha)
#     R2 = getC(beta)
#     R3 = getD(gamma)
#     M = R3 * R2 * R1
#     # print M
#     # print("###", newCoor)
#     for i, c in enumerate(newCoor):
#         # print np.asarray(M*np.matrix(c).T)
#         #newCoor[i] = np.asarray((M * c.T).T)
#         newCoor[i] = np.asarray((M * np.matrix(c).T).T)
#         # print c, newCoor[i]
#     print("###", newCoor)
#     # print("###", np.dot(n2, M))
#     # raise RuntimeError()
#     return newCoor
