# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Cadishi preprocessor dummy filter.
"""
from __future__ import print_function


import time
import random
from cadishi import base


class Dummy(base.Filter):
    """A filter that does nothing but forwarding base.Container() objects.  May
    be used as a basis to write more complicated filters and for debugging.
    """
    _depends = []
    _conflicts = []

    def __init__(self, source=-1, verbose=False, sleep_seconds=0, raise_exception=False):
        self.src = source
        self.verb = verbose
        # debug option: introduces a sleep() at each iteration
        self.sleep_seconds = sleep_seconds
        # debug option: raises a RuntimeError() exception after 3 to 6 seconds
        self.raise_exception = raise_exception
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
            if frame is not None:
                assert isinstance(frame, base.Container)
                if self.sleep_seconds > 0:
                    time.sleep(self.sleep_seconds)
                if self.raise_exception:
                    sleep_s = random.randrange(3, 7)
                    time.sleep(sleep_s)
                    raise RuntimeError("test exception raised by Dummy filter")
                frame.put_meta(self.get_meta())
                if self.verb:
                    print("Dummy.next() :", frame.i)
            yield frame
