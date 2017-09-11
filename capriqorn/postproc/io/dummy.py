# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Capriqorn dummy IO.
"""


import string
import numpy as np
from six.moves import range
from cadishi import base


class DummyReader(base.Reader):
    """
    Dummy histogram reader.  Provides a source for some histogram
    sets, each containing some histograms with randomly populated bins.
    """
    _depends = []
    _conflicts = []

    def __init__(self, n_histogram_sets=10, n_el=3, n_bins=1024,
                 n_virtual=0, random=True, shell=False, verbose=False):
        self.count = 1
        self.n_histogram_sets = n_histogram_sets
        self.n_el = n_el
        self.n_bins = n_bins
        self.n_virtual = n_virtual
        self.random = random
        self.shell = shell
        self.verb = verbose
        # ---
        self._depends.extend(super(base.Reader, self)._depends)
        self._conflicts.extend(super(base.Reader, self)._conflicts)

    def get_meta(self):
        """
        Return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information.
        """
        meta = {}
        label = 'DummyReader'
        param = {}
        meta[label] = param
        return meta

    def next(self):
        while (self.count <= self.n_histogram_sets):
            hs = base.Container(number=self.count)
            dr = 0.01
            radii = np.array([dr * (0.5 + x) for x in range(self.n_bins)])
            hs.put_data(base.loc_histograms + '/radii', radii)
            # --- fill histogram set with dummy data
            spec_list = (list(string.ascii_uppercase))[:self.n_el]
            for i in range(1, self.n_virtual + 1):
                x = 'X' + str(i)
                spec_list.append(x)
            if self.shell:
                spec_list[:] = spec_list + [x + '.s' for x in spec_list]
            for i in range(len(spec_list)):
                for j in range(i, len(spec_list)):
                    key = spec_list[i] + "," + spec_list[j]
                    if self.random:
                        histo = np.random.rand(self.n_bins)
                    else:
                        histo = np.ones(self.n_bins)
                    hs.put_data(base.loc_histograms + '/' + key, histo)
            # ---
            if self.verb:
                print "DummyReader.next() :", self.count
            hs.put_meta(self.get_meta())
            yield hs
            self.count += 1
            del hs


class DummyWriter(base.Writer):
    """Dummy trajectory writer. Provides a sink for the pipeline, simply
    discards the base.Container() instances it gets from the generators in the
    pipeline."""
    _depends = []
    _conflicts = []

    def __init__(self, source, verbose=False):
        self.src = source
        self.verb = verbose
        # ---
        self._depends.extend(super(base.Writer, self)._depends)
        self._conflicts.extend(super(base.Writer, self)._conflicts)

    def dump(self):
        for obj in self.src.next():
            if obj is not None:
                if self.verb:
                    print "DummyWriter.dump() : ", obj.i
                pass
