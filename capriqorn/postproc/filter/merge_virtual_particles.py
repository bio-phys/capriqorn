# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Capriqorn merge virtual particles filter.

NOTE: The merge functionality is actually implemented in free functions,
      see <selection.py>.  While this file provides a filter, it is
      probably more useful to apply the free functions whenever needed.
"""
from __future__ import print_function


from cadishi import base
from cadishi import util

from ...lib import selection


class MergeVirtualParticles(base.Filter):
    """A filter that merges species of virtual particles
    in base.Container() instances."""
    _depends = []
    _conflicts = []

    def __init__(self, source=-1, verbose=False):
        self.src = source
        self.verb = verbose
        # ---
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """
        Return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information.
        """
        meta = {}
        label = 'MergeVirtualParticles'
        param = {}
        meta[label] = param
        return meta

    def next(self):
        for frm in self.src.next():
            if frm is not None:
                assert isinstance(frm, base.Container)
                # ---
                histos = frm.get_data(base.loc_histograms)
                elements = util.get_elements(list(histos.keys()))
                if ('X1' in elements) and ('X2' in elements):
                    selection.merge_virtual_particles(frm)
                # ---
                frm.put_meta(self.get_meta())
                if self.verb:
                    print("MergeVirtualParticles.next() :", frm.i)
                yield frm
            else:
                yield None
