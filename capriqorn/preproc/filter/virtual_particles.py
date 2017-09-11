# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
# 
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN 
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

"""capriqorn filter library <preproc_filter_sphere.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""

import numpy as np
import numpy.random as ran
from six.moves import range
import cadishi.base as base
from ...lib import rotate as rot

# --- use fast Cython functions for time critical parts, if available
try:
    from capriqorn.kernel import c_virtual_particles
    have_c_virtual_particles = True
except:
    have_c_virtual_particles = False
    print(" Note: capriqorn.preproc.filter.virtual_particles: could not import c_virtual_particles")


def _genIdealGas(N, L):
    """
    Generate a set of random coordinate triples.
    Serves as a helper function for the virtual particles method.
    """
    l = L / 2.
    coordinates = np.column_stack((ran.uniform(-l, l, N),
                                   ran.uniform(-l, l, N),
                                   ran.uniform(-l, l, N)))
    return coordinates


if have_c_virtual_particles:
    _genLattice = c_virtual_particles.genLattice
else:
    def _genLattice(gridLength, latticeConstant, noise=False):
        """
        Generate a 3D lattice, optionally with random displacement.
        Serves as a helper function for the virtual particles method.
        """
        base = np.zeros((3, 3))
        base[0, 0] = latticeConstant
        base[1, 1] = latticeConstant
        base[2, 2] = latticeConstant
        alpha = np.random.uniform(0, 2 * np.pi)
        beta = np.arccos(np.random.uniform(-1, 1))
        gamma = np.random.uniform(0, 2 * np.pi)
        baseNew = rot.rotate(base, alpha, beta, gamma)
        lattice = np.zeros((gridLength ** 3, 3))
        l_half = gridLength / 2
        counter = 0
        for i in range(gridLength):
            for j in range(gridLength):
                for k in range(gridLength):
                    vec = np.asarray([i, j, k], dtype=np.float) - l_half
                    lattice[counter] = vec[0] * baseNew[0, :] \
                        + vec[1] * baseNew[1, :] \
                        + vec[2] * baseNew[2, :]
                    if noise is True:
                        lattice[counter] += 0.5 * (ran.uniform(-1, 1) * baseNew[0, :]
                                                   + ran.uniform(-1, 1) * baseNew[1, :]
                                                   + ran.uniform(-1, 1) * baseNew[2, :])
                    counter += 1
        offset = ran.uniform(-latticeConstant / 2., latticeConstant / 2., 3)
        lattice[:] += offset
        return lattice


class VirtualParticles(base.Filter):
    """A filter that adds virtual particles to coordinate sets
    in base.Container() instances."""
    _depends = []
    _conflicts = []

    def __init__(self,
                 source=-1,
                 method='lattice',
                 x_box_length=80.0,
                 x_density=0.1,
                 noise=False,
                 label='X',
                 random_seed=0,
                 verbose=False):
        self.src = source
        self.verb = verbose
        assert (method is not None)
        assert (method in ["lattice", "gas"])
        assert (x_box_length is not None)
        assert (x_density is not None)
        # --- compute derived quantities
        if (method == "lattice"):
            xD = (2. / x_density) ** (1. / 3.)  # we'll generate two lattices, each with half the density
            x_box_length = int(round(x_box_length / xD))
            x_box_length += x_box_length % 2
            xN = x_box_length ** 3
        elif (method == "gas"):
            xN = int(round(x_box_length ** 3 * x_density))
        else:
            raise ValueError('Unknown virtual particle method requested : ' +
                             self.method)
        # --- save initialization parameters
        self.method = method
        self.xN = xN
        self.x_box_length = x_box_length
        self.x_density = x_density
        self.noise = noise
        self.label = label
        self.random_seed = random_seed
        if (method == "lattice"):
            self.xD = xD
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)
        # Positive values of random_seed are used as a seed to the numpy random number
        # generator in order to achieve reproducibility.
        if (random_seed > 0):
            np.random.seed(random_seed)

    def get_meta(self):
        """
        Return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information.
        """
        meta = {}
        label = 'VirtualParticles'
        param = {'method': self.method}
        param['x_box_length'] = self.x_box_length
        param['x_density'] = self.x_density
        param['noise'] = self.noise
        param['label'] = self.label
        param['random_seed'] = self.random_seed
        meta[label] = param
        return meta

    def next(self):
        for frm in self.src.next():
            if frm is not None:
                assert isinstance(frm, base.Container)
                # --- add virtual particles
                if (self.method == "lattice"):
                    if self.verb:
                        print "VirtualParticles : adding 2x " + str(self.x_box_length ** 3) \
                            + " lattice particles"
                    for i in [1, 2]:
                        coords = _genLattice(self.x_box_length, self.xD, noise=self.noise)
                        frm.put_data(base.loc_coordinates + '/' + self.label + str(i), coords)
                elif (self.method == "gas"):
                    coords = _genIdealGas(self.xN, self.x_box_length)
                    frm.put_data(base.loc_coordinates + '/' + self.label, coords)
                #
                frm.put_meta(self.get_meta())
                if self.verb:
                    print "VirtualParticles.next() :", frm.i
            # yield modified frame, or simply pass through None
            yield frm
