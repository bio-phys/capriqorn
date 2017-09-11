# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
# 
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN 
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

"""capriqorn filter library <postproc_filter_strip_virtual_particles.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""

from cadishi import base
from cadishi import util


# constant list of keys to be removed from the histograms dictionary
blacklist = ["X1,X1", "X2,X2", "X1.s,X1.s", "X2.s,X2.s",
             "X1,X1.s", "X2,X2.s", "X1.s,X1", "X2.s,X2"]


class StripVirtualParticles(base.Filter):
    """
    A filter that strips certain combinations of virtual particles
    from base.Container() instances, typically distance histograms.
    """
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
        Return information on the present filter, ready to be added to a frame
        object's list of pipeline meta information.
        """
        meta = {}
        label = 'StripVirtualParticles'
        param = {}
        meta[label] = param
        return meta

    def next(self):
        for frm in self.src.next():
            if frm is not None:
                assert isinstance(frm, base.Container)
                histgrms = frm.get_data(base.loc_histograms)
                elements = util.get_elements(histgrms.keys())
                if ('X1' in elements) and ('X2' in elements):
                    for key in blacklist:
                        if key in histgrms.keys():
                            del histgrms[key]
                frm.put_meta(self.get_meta())
                if self.verb:
                    print "StripVirtualParticles.next() :", frm.i
                yield frm
            else:
                yield None
