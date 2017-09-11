# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Capriqorn Dummy filter.
"""

from cadishi import base


class Dummy(base.Filter):
    """a filter that does nothing"""
    _depends = []
    _conflicts = []

    def __init__(self, source=-1, verbose=False):
        self.src = source
        self.verb = verbose
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """
        return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information
        """
        meta = {}
        label = 'Dummy'
        param = {}
        meta[label] = param
        return meta

    def next(self):
        for obj in self.src.next():
            if obj is not None:
                if self.verb:
                    print "Dummy.next() :", obj.i
                yield obj
            else:
                yield None
