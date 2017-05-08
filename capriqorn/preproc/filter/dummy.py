"""Cadishi preprocessor dummy filter

This file is part of the Cadishi package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


__author__ = "Juergen Koefinger, Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2016 Juergen Koefinger, Klaus Reuter"
__license__ = "license_tba"


from cadishi import base


class Dummy(base.Filter):
    """A filter that does nothing but forwarding base.Container() objects.  May
    be used as a basis to write more complicated filters and for debugging.
    """
    _depends = []
    _conflicts = []

    def __init__(self, source=-1, verbose=False):
        self.src = source
        self.verb = verbose
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """ Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information.
        """
        meta = {}
        label = 'Dummy'
        param = {}
        meta[label] = param
        return meta

    def next(self):
        for frame in self.src.next():
            assert isinstance(frame, base.Container)
            frame.put_meta(self.get_meta())
            if self.verb:
                print "Dummy.next() :", frame.i
            yield frame
