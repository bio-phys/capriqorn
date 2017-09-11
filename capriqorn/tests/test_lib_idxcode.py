# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Tests for the idxcode module."""


from ..lib import idxcode

def test_idxcode():
    for i in range(-3, 4):
        for j in range(-3, 4):
            for k in range(-3, 4):
                value = idxcode.encode_indices(i, j, k)
                (ii, jj, kk) = idxcode.decode_indices(value)
                assert(i == ii)
                assert(j == jj)
                assert(k == kk)
