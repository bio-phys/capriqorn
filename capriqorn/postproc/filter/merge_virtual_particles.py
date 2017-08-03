"""capriqorn filter library <postproc_filter_merge_virtual_particles.py>

NOTE: The merge functionality is actually implemented in free functions,
      see <selection.py>.  While this file provides a filter, it is
      probably more useful to apply the free functions whenever needed.

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


from cadishi import base
from cadishi import util

from ...lib import selection


class MergeVirtualParticles(base.Filter):
    """A filter that merges species of virtual particles
    in base.Container() instances."""
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
        Return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information.
        """
        meta = {}
        label = 'MergeVirtualParticles'
        param = {}
        meta[label] = param
        return meta

    def next(self):
        for frm in self.src.next():
            if frm is not None:
                assert isinstance(frm, base.Container)
                # ---
                histos = frm.get_data(base.loc_histograms)
                elements = util.get_elements(histos.keys())
                if ('X1' in elements) and ('X2' in elements):
                    selection.merge_virtual_particles(frm)
                # ---
                frm.put_meta(self.get_meta())
                if self.verb:
                    print "MergeVirtualParticles.next() :", frm.i
                yield frm
            else:
                yield None
