# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
# 
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN 
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

"""capriqorn filter library <preproc_filter_cuboid.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


import numpy as np
import copy
import cadishi.base as base


class Cuboid(base.Filter):
    """a filter that selects particles within an cuboidal volume"""
    _depends = []
    _conflicts = []

    def __init__(self, half_lengths=[1.e6, 1.e6, 1.e6], shell_width=-1, source=-1,
                 verbose=False):
        assert (len(half_lengths) == 3)
        assert ((half_lengths[0] > 0.0) and (half_lengths[1] > 0.0) and (half_lengths[2] > 0.0))
        self.half_lengths = np.array(half_lengths)
        self.shell_width = shell_width
        # ---
        L = 2.0 * np.array(half_lengths)
        self.r_max = 2.0 * np.sqrt((self.half_lengths ** 2).sum())
        self.volume = L.prod()
        self.shell_volume = self.volume - (L - 2 * shell_width).prod()
        # ---
        self.src = source
        self.verb = verbose
        # ---
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """
        return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information
        """
        meta = {}
        label = 'Cuboid'
        param = {'half_lengths': self.half_lengths.tolist(),
                 'shell_width': self.shell_width,
                 'volume': self.volume,
                 'shell_volume': self.shell_volume,
                 'r_max': self.r_max}
        meta[label] = param
        return meta

    def selectBody(self, coords, half_lengths=None):
        """ Return indices of the particles within the cuboid defined by its
        semi-principal axes. """
        if half_lengths is None:
            half_lengths = self.half_lengths
        else:
            half_lengths = np.array(half_lengths)
        assert (len(half_lengths) == 3)
        assert ((half_lengths[0] > 0.0) and (half_lengths[1] > 0.0) and (half_lengths[2] > 0.0))
        # ---
        q_within_body = (np.fabs(coords[:, 0]) < half_lengths[0]) \
            * (np.fabs(coords[:, 1]) < half_lengths[1]) \
            * (np.fabs(coords[:, 2]) < half_lengths[2])
        indices = np.where(q_within_body)
        return indices

    def selectShell(self, coords, half_lengths=None, sw=None):
        """
        Return indices of the particles within the shell region of
        the cuboid defined by its semi-principal axes.
        """
        if half_lengths is None:
            half_lengths = self.half_lengths
        else:
            half_lengths = np.array(half_lengths)
        assert (len(half_lengths) == 3)
        assert ((half_lengths[0] > 0.0) and (half_lengths[1] > 0.0) and (half_lengths[2] > 0.0))
        sw = sw or self.shell_width
        assert (sw > 0.0)
        assert (min(half_lengths) > sw)
        # ---
        q_within_body = (np.fabs(coords[:, 0]) < half_lengths[0]) \
            * (np.fabs(coords[:, 1]) < half_lengths[1]) \
            * (np.fabs(coords[:, 2]) < half_lengths[2])
        # ---
        q_outside_core = (np.fabs(coords[:, 0]) >= half_lengths[0] - sw) \
            + (np.fabs(coords[:, 1]) >= half_lengths[1] - sw) \
            + (np.fabs(coords[:, 2]) >= half_lengths[2] - sw)

        # determine cut-set
        indices = np.where(np.logical_and(q_within_body, q_outside_core))
        return indices

    def selectCore(self, coords, half_lengths=None, sw=None):
        """
        Return indices of the particles within the core region of the cuboid
        defined by its semi-principal axes minus the shell width.
        """
        if half_lengths is None:
            half_lengths = self.half_lengths
        else:
            half_lengths = np.array(half_lengths)
        assert (len(half_lengths) == 3)
        assert ((half_lengths[0] > 0.0) and (half_lengths[1] > 0.0) and (half_lengths[2] > 0.0))
        sw = sw or self.shell_width
        assert (sw > 0.0)
        assert (min(half_lengths) > sw)
        indices = self.selectBody(coords, (half_lengths[:] - sw))
        return indices

    def next(self):
        for frm_in in self.src.next():
            if frm_in is not None:
                assert isinstance(frm_in, base.Container)
                frm_out = copy.deepcopy(frm_in)
                frm_out.del_data(base.loc_coordinates)
                # ---
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
                # ---
                frm_out.i = frm_in.i
                # ---
                frm_out.put_data('log', frm_in.get_data('log'))
                frm_out.put_meta(self.get_meta())
                if self.verb:
                    print "Cuboid.next() :", frm_out.i
            else:
                frm_out = None
            yield frm_out
