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
