# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Capriqorn preprocessor step filter.
"""
from __future__ import print_function


import cadishi.base as base


class Step(base.Filter):
    """A filter that skips frames."""
    _depends = []
    _conflicts = []

    def __init__(self, step=1, source=-1, verbose=False):
        self.src = source
        self.step = step
        self.verb = verbose
        self.count = 0
        # ---
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information.
        """
        meta = {}
        label = 'Step'
        param = {'step': self.step}
        meta[label] = param
        return meta

    def next(self):
        for frm in self.src.next():
            if frm is not None:
                if (self.count % self.step == 0):
                    assert isinstance(frm, base.Container)
                    frm.put_meta(self.get_meta())
                    if self.verb:
                        print("Step.next() :", frm.i)
                    yield frm
                else:
                    pass
                self.count += 1
            else:
                yield None
