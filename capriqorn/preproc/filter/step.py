"""Capriqorn preprocessor step filter

This file is part of the Capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


__author__ = "Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2016 Klaus Reuter"
__license__ = "license_tba"


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
            if (self.count % self.step == 0):
                assert isinstance(frm, base.Container)
                frm.put_meta(self.get_meta())
                if self.verb:
                    print "Step.next() :", frm.i
                yield frm
            else:
                pass
            self.count += 1
