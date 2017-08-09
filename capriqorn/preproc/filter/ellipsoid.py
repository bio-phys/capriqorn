"""capriqorn filter library <preproc_filter_ellipsoid.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


import math
import numpy as np
import copy
import cadishi.base as base


class Ellipsoid(base.Filter):
    """a filter that selects particles within an ellipsoidal volume"""
    _depends = []
    _conflicts = []

    def __init__(self, semi_principal_axes=[1.e6, 1.e6, 1.e6], shell_width=-1,
                 source=-1, verbose=False):
        assert (len(semi_principal_axes) == 3)
        self.semi_principal_axes = np.array(semi_principal_axes)  # semi-principal axes
        self.shell_width = shell_width
        # ---
        self.r_max = 2. * np.max(self.semi_principal_axes)
        self.volume = 4. / 3. * math.pi * self.semi_principal_axes.prod()
        self.shell_volume = self.volume - 4. / 3. * math.pi * (self.semi_principal_axes - self.shell_width).prod()
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
        label = 'Ellipsoid'
        param = {'semi_principal_axes': self.semi_principal_axes.tolist(),
                 'shell_width': self.shell_width,
                 'volume': self.volume,
                 'shell_volume': self.shell_volume,
                 'r_max': self.r_max}
        meta[label] = param
        return meta

    def selectBody(self, coords, semi_principal_axes=None):
        """
        Return indices of the particles within the
        ellipsoid defined by its semi-principal axes.
        """
        if semi_principal_axes is None:
            semi_principal_axes = self.semi_principal_axes
        else:
            semi_principal_axes = np.array(semi_principal_axes)
        assert (len(semi_principal_axes) == 3)
        # ---
        semi_principal_axes_sq = semi_principal_axes ** 2
        q_within_body = (coords ** 2 / semi_principal_axes_sq[np.newaxis, :]).sum(axis=1) < 1.0
        indices = np.where(q_within_body)
        return indices

    def selectShell(self, coords, semi_principal_axes=None, sw=None):
        """
        Return indices of the particles within the shell region of
        the ellipsoid defined by its semi-principal axes.
        """
        if semi_principal_axes is None:
            semi_principal_axes = self.semi_principal_axes
        else:
            semi_principal_axes = np.array(semi_principal_axes)
        assert (len(semi_principal_axes) == 3)
        sw = sw or self.shell_width
        assert (sw > 0.0)
        assert (min(semi_principal_axes) > sw)
        coords_sq = coords ** 2
        # select body
        semi_principal_axes_sq = semi_principal_axes ** 2
        q_within_body = (coords_sq / semi_principal_axes_sq[np.newaxis, :]).sum(axis=1) < 1.0
        # select core
        semi_principal_axes_sq = (semi_principal_axes[:] - sw) ** 2
        q_outside_core = (coords_sq / semi_principal_axes_sq[np.newaxis, :]).sum(axis=1) >= 1.0
        # determine cut-set
        indices = np.where(np.logical_and(q_within_body, q_outside_core))
        return indices

    def selectCore(self, coords, semi_principal_axes=None, sw=None):
        """
        Return indices of the particles within the core region of the ellipsoid
        defined by its semi-principal axes minus the shell width.
        """
        if semi_principal_axes is None:
            semi_principal_axes = self.semi_principal_axes
        else:
            semi_principal_axes = np.array(semi_principal_axes)
        assert (len(semi_principal_axes) == 3)
        sw = sw or self.shell_width
        assert (sw > 0.0)
        assert (min(semi_principal_axes) > sw)
        indices = self.selectBody(coords, (semi_principal_axes[:] - sw))
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
                # ---
                if self.verb:
                    print "Ellipsoid.next() :", frm_out.i
            else:
                frm_out = None
            yield frm_out
