# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
# 
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN 
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

import six

from numpy.testing import assert_array_equal, assert_equal

from capriqorn.testing import data
from capriqorn.lib import formFactor


def test_readAtomSFParam(data):
    form_factor = formFactor.readAtomSFParam(data['atomsf.dat'])
    assert len(form_factor) == 12
    assert_array_equal(
        sorted(form_factor.keys()), ('C', 'Cl', 'Cl-1', 'Fe', 'Fe+2', 'Fe+3',
                                     'H', 'N', 'Na', 'Na+1', 'O', 'S'))
    for factor in six.itervalues(form_factor):
        assert len(factor) == 4
        assert len(factor[0]) == 3
        assert len(factor[1]) == 4
        assert len(factor[2]) == 4
        assert len(factor[3]) == 4
    # check for one entry the exact values and then assume the others work too
    assert_array_equal(form_factor['S'][0], [16, 16, 0.8669])
    assert_array_equal(form_factor['S'][1:],
                       [[6.9053, 5.2034, 1.4379, 1.58630],
                        [1.4679, 22.215099, .253600, 56.172001],
                        [0.319, 0.557, 0.110, 0.124]])


def test_writeAtomSFParam(data, tmpdir):
    form_factor = formFactor.readAtomSFParam(data['atomsf.dat'])
    with tmpdir.as_cwd():
        formFactor.writeAtomSFParam(form_factor, 'testsf.dat')
        written = formFactor.readAtomSFParam('testsf.dat')
        # does a deep comparison
        assert_equal(form_factor, written)
