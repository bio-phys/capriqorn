# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Cadishi preprocessor xyz filter/writer.
"""


import math
import numpy as np
from six.moves import range

import cadishi.base as base
import cadishi.util as util


class XYZ(base.Filter):
    """A filter that writes particle coordinates into text files, one per frame,
    from a generator returning base.Container with coordinate data."""
    _depends = []
    _conflicts = []

    def __init__(self, source=-1,
                 file_prefix='',
                 output_directory='./preprocessor_output',
                 first_frame_only=False,
                 verbose=False):
        self.src = source
        if not isinstance(file_prefix, basestring):
            file_prefix = ''
        self.file_prefix = file_prefix
        if not isinstance(output_directory, basestring):
            output_directory = './preprocessor_output'
        self.output_directory = output_directory.rstrip('/') + '/'
        self.first_frame_only = first_frame_only
        self.verb = verbose
        # ---
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information.
        """
        meta = {}
        label = 'XYZ'
        param = {'output_directory': self.output_directory,
                 'file_prefix': self.file_prefix,
                 'first_frame_only': self.first_frame_only}
        meta[label] = param
        return meta

    def next(self):
        do_write = True
        util.md(self.output_directory)
        for frm_in in self.src.next():
            if frm_in is not None:
                assert isinstance(frm_in, base.Container)
                # ---
                if (do_write):
                    volCrds = []
                    volSpecies = []
                    elements = frm_in.get_keys(base.loc_coordinates, skip_keys='radii')
                    for el in elements:
                        coord_set = frm_in.get_data(base.loc_coordinates + '/' + el)
                        for ij in range(coord_set.shape[0]):
                            triple = coord_set[ij, :]
                            volCrds.append(triple)
                            volSpecies.append(el)
                    file_name = self.output_directory + self.file_prefix + "%08d.xyz" % frm_in.i
                    util.write_xyzFile(volCrds, volSpecies, file_name)
                    if self.first_frame_only:
                        do_write = False
                # ---
                frm_out = frm_in
                frm_out.put_meta(self.get_meta())
                if self.verb:
                    print "XYZ.next() :", frm_out.i
            else:
                frm_out = None
            yield frm_out
