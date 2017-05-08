"""capriqorn preprocessor IO, dummy reader/writer

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""
import copy
import numpy as np

from cadishi import base


__author__ = "Juergen Koefinger, Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2016 Juergen Koefinger, Klaus Reuter"
__license__ = "license_tba"


class DummyReader(base.Reader):
    """Dummy trajectory reader, provides a source for frames with -- among
    others -- random coordinates.  Useful for unit testing.
    """
    _depends = []
    _conflicts = []

    def __init__(self, n_frames=3, n_elems=3, n_atoms=1024, verbose=False):
        self.n_frames = n_frames
        self.n_elems = n_elems
        self.n_atoms = n_atoms
        self.verb = verbose
        self.frms = []
        # ---
        self._depends.extend(super(base.Reader, self)._depends)
        self._conflicts.extend(super(base.Reader, self)._conflicts)
        # ---
        for i in range(n_frames):
            frm = base.Container(number=i)
            for j in range(n_elems):
                s_name = "El" + str(i) + str(j)
                s_coor = np.random.rand(n_atoms, 3)
                frm.put_data(base.loc_coordinates + '/' + s_name, s_coor)
            s_name = 'my/huge/table/in/some/subdirectory/data'
            s_table = np.random.rand(n_atoms, n_atoms)
            frm.put_data(s_name, s_table)
            s_name = 'integer'
            frm.put_data(s_name, 1)
            s_name = 'string'
            frm.put_data(s_name, 'Banana Joe')
            s_name = 'float'
            frm.put_data(s_name, 3.14)
            s_name = 'Python integer list'
            frm.put_data(s_name, [1, 2, 3, 4, 5, 6])
            s_name = 'Python float list'
            frm.put_data(s_name, [1., 2., 3., 4., 5., 6.])
            s_name = 'Python string list'
            frm.put_data(s_name, ['Hello', 'World'])
            s_name = 'Python mixed list'
            frm.put_data(s_name, ['Hello', 1])
            self.frms.append(copy.deepcopy(frm))

    def get_meta(self):
        """ Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information. """
        meta = {}
        label = 'DummyReader'
        param = {}
        meta[label] = param
        return meta

    def next(self):
        for frm in self.frms:
            frm.put_meta(self.get_meta())
            if self.verb:
                print "DummyReader.next() :", frm.i
            yield frm


class DummyWriter(base.Writer):
    """Dummy trajectory writer, provides a sink for a pipeline, does nothing.
    """
    _depends = []
    _conflicts = []

    def __init__(self, source, verbose=False):
        self.src = source
        self.verb = verbose
                # ---
        self._depends.extend(super(base.Writer, self)._depends)
        self._conflicts.extend(super(base.Writer, self)._conflicts)

    def dump(self):
        for frm in self.src.next():
#             print '###'
#             print '###', frm.i
#             print '###', frm.data
#             print '###'
            if self.verb:
                print "DummyWriter.dump() : ", frm.i
            pass
