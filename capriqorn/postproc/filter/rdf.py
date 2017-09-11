# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
# 
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN 
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

"""Capriqorn postprocessor module to perform the RDF computation.
"""
# This file is part of the capriqorn package.  See README.rst,
# LICENSE.txt, and the documentation for details.


# TODO: catch runtime assertions, use meaningful error messages


import numpy as np
from six.moves import range

from cadishi import base
from cadishi import util


class RDF(base.Filter):
    """RDF computation filter."""
    _depends = []
    _conflicts = []

    def __init__(self, source=-1, verbose=False):
        self.src = source
        self.verb = verbose
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """Return information on the present filter, ready to be added
        to a frame object's list of pipeline meta information.
        """
        meta = {}
        label = 'RDF'
        param = {}
        meta[label] = param
        return meta

    def _process_frame(self, frm):
        """Compute the radial distribution function.
        """
        # This implementation follows <legacy/getRDFFromPBC.py> by Juergen Koefinger

        assert(frm.has_key(base.loc_volumes))
        assert(frm.has_key(base.loc_nr_particles))
        # obtain array of box volumes from the original trajectory frames
        _volumes = frm.get_data(base.loc_volumes)
        box_volumes = _volumes['box']
        if hasattr(box_volumes, "__len__"):
            n_samples = len(box_volumes)
        else:
            n_samples = 1
        # obtain arrays of the numbers of particles present in the original trajectory frame
        nr_particles = frm.get_data(base.loc_nr_particles)
        for key in nr_particles:
            assert(n_samples == (nr_particles[key]).shape[0])
        histograms = frm.get_data(base.loc_histograms)
        dr = frm.query_meta('histograms/histogram/dr')
        # consistency check if the histogram labels match with the particle numbers
        _species_h = set(util.get_elements(histograms.keys()))
        _species_p = set(nr_particles.keys())
        assert(_species_h == _species_p)

        radii = histograms['radii']
        histogram_keys = histograms.keys()
        histogram_keys.remove('radii')

        vol = np.sum(box_volumes)
        vol /= n_samples  # QUESTION: 'norm' in the original code, is this just the number of samples?
        vol_inv = np.sum(np.reciprocal(box_volumes))
        vol_inv /= n_samples  # QUESTION: 'norm' in the original code, is this just the number of samples?

        # coefficients repeatedly used by the nested loop below
        coeff = 4.0 * np.pi * dr * vol_inv * np.multiply(radii, radii)

        rdf = {}
        for key in histogram_keys:
            species_1, species_2 = tuple(key.split(','))
            nr_1 = np.sum(nr_particles[species_1]) / float(n_samples)
            nr_2 = np.sum(nr_particles[species_2]) / float(n_samples)
            # the particle number in the box is constant, therefor densities are calculated as
            rho_1 = nr_1 * vol_inv
            rho_2 = nr_2 * vol_inv
            if (nr_1 * nr_2 > 0):
                if (species_1 == species_2):
                    fac = 1.0
                else:
                    fac = 2.0
                histo = np.copy(histograms[key])
                for i in range(len(radii)):
                    histo[i] /= fac * nr_1 * nr_2 * coeff[i]
                # Factor 2 because distances are only counted once in histograms (r_{ij} and r_{ji} are counted as a single distance)
                rdf[key] = 2 * histo
                if (species_1 == species_2):
                    rdf[key][0] = rho_1
            else:
                if self.verb:
                    print " RDF: skipping " + key
        rdf['radii'] = radii
        # ---
        if self.verb:
            print " RDF: average inverse volume =", vol_inv
            print " RDF: inverse average volume =", 1. / vol
            print " RDF: ratio =", vol_inv * vol
        # ---
        frm.put_data(base.loc_rdf, rdf)

    def next(self):
        for frm in self.src.next():
            if frm is not None:
                self._process_frame(frm)
                frm.put_meta(self.get_meta())
                if self.verb:
                    print "RDF.next() :", frm.i
                yield frm
            else:
                yield None
