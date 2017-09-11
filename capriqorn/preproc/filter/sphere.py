# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Cadishi preprocessor sphere geometry filter.
"""


import math
import numpy as np
from six.moves import range
import copy
import cadishi.base as base


class Sphere(base.Filter):
    """A filter that selects particles within a spherical volume
    from a generator returning base.Container with coordinate data."""
    _depends = []
    _conflicts = []

    def __init__(self,
                 radius=1.e6,
                 shell_width=-1,
                 do_len_histo=True,
                 len_histo_dr=0.01,
                 source=-1,
                 verbose=False):
        self.radius = radius
        self.shell_width = shell_width
        # ---
        self.volume = 4. / 3. * math.pi * radius ** 3
        self.r_max = 2. * radius
        if (shell_width > 0.0):
            self.shell_volume = self.volume - 4. * math.pi / 3. * (radius - shell_width) ** 3
        else:
            self.shell_volume = None
        # ---
        self.do_len_histo = do_len_histo
        self.len_histo_dr = len_histo_dr
        self.src = source
        self.verb = verbose
        # ---
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information.
        """
        meta = {}
        label = 'Sphere'
        param = {'radius': self.radius,
                 'shell_width': self.shell_width,
                 'do_len_histo': self.do_len_histo,
                 'len_histo_dr': self.len_histo_dr,
                 'volume': self.volume,
                 'shell_volume': self.shell_volume,
                 'r_max': self.r_max}
        meta[label] = param
        return meta

    def selectBody(self, coords, R=None):
        """Return indices of the particles within the sphere of radius R.
        """
        # --- a trick to bypass the self restriction on default arguments
        R = R or self.radius
        # ---
        lengthsSqr = (coords ** 2).sum(axis=1)
        indices = np.where(lengthsSqr < R ** 2)
        return indices

    def selectShell(self, coords, R=None, sw=None):
        """Return indices of the particles within the spherical shell of
        inner radius (R-sw) and outer radius R, ie the shell.
        """
        R = R or self.radius
        sw = sw or self.shell_width
        assert (R > sw)
        lengthsSqr = (coords ** 2).sum(axis=1)
        indices = np.where(np.logical_and(lengthsSqr >= (R - sw) ** 2,
                                          lengthsSqr < R ** 2))
        return indices

    def selectCore(self, coords, R=None, sw=None):
        """Return indices of the particles within the sphere of
        radius (R-sw), ie the core.
        """
        R = R or self.radius
        sw = sw or self.shell_width
        assert (R > sw)
        indices = self.selectBody(coords, R - sw)
        return indices

    def next(self):
        for frm_in in self.src.next():
            if frm_in is not None:
                assert isinstance(frm_in, base.Container)
                frm_out = copy.deepcopy(frm_in)
                frm_out.del_data(base.loc_coordinates)
                frm_out.del_data(base.loc_len_histograms)
                if self.do_len_histo:
                    n_bins = int(round(self.radius / self.len_histo_dr))
                    radii = np.zeros(n_bins)
                    for i in range(n_bins):
                        radii[i] = (0.5 + np.float64(i)) * self.len_histo_dr
                    frm_out.put_data(base.loc_len_histograms + '/radii', radii)
                for spec_id in frm_in.get_keys(base.loc_coordinates, skip_keys='radii'):
                    coord_in = frm_in.get_data(base.loc_coordinates + '/' + spec_id)
                    if (self.shell_width > 0.0):
                        # --- select core particles
                        indices = self.selectCore(coord_in)
                        coord_out = coord_in[indices]
                        frm_out.put_data(base.loc_coordinates + '/' + spec_id,
                                         coord_out)
                        # --- select shell particles
                        indices = self.selectShell(coord_in)
                        coord_out = coord_in[indices]
                        frm_out.put_data(base.loc_coordinates + '/' + spec_id + '.s',
                                         coord_out)
                    else:
                        indices = self.selectBody(coord_in)
                        coord_out = coord_in[indices]
                        frm_out.put_data(base.loc_coordinates + '/' + spec_id,
                                         coord_out)
                    if self.do_len_histo:
                        indices = self.selectBody(coord_in)
                        len_arr = np.sqrt((coord_in[indices] ** 2).sum(axis=1))
                        (histo, _edges) = np.histogram(len_arr, bins=n_bins,
                                                       range=(0.0, self.radius))
                        histo_float64 = histo.astype(np.float64)
                        frm_out.put_data(base.loc_len_histograms + '/' + spec_id,
                                         histo_float64)
                frm_out.i = frm_in.i
                frm_out.put_data('log', frm_in.get_data('log'))
                frm_out.put_meta(self.get_meta())
                if self.verb:
                    print "Sphere.next() :", frm_out.i
            else:
                frm_out = None
            yield frm_out
