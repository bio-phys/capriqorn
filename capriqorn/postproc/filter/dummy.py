"""Capriqorn filter library <postproc_filter_dummy.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
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
