"""capriqorn filter library <preproc_filter_refstruct.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""

import MDAnalysis as mda
import numpy as np
import copy
from cadishi import base
from ...lib import refstruct as librefstruct


class ReferenceStructure(base.Filter):
    """
    A filter that selects particles within a volume defined by a reference
    structure from a generator returning base.Container with coordinate data.
    """
    _depends = []
    _conflicts = []

    def __init__(self,
                 topology_file=None,  # reference structure PDB file
                 selection='all',
                 distance=10,  # distance from reference structure
                 shell_width=-1,
                 algorithm="brute_force",
                 source=-1,
                 verbose=False):
        self.topology_file = topology_file
        self.selection = selection
        self.distance = distance
        self.shell_width = shell_width
        self.algorithm = algorithm
        librefstruct.set_algorithm(algorithm)
        # ---
        universe = mda.Universe(topology_file)
        self.atoms = universe.atoms.select_atoms(selection)
        # --- calculate r_max from longest distance in reference structure
        d_max = librefstruct.maxInnerDistance(self.atoms.positions)
        self.r_max = d_max + 3. * self.distance
        # ---
        self.src = source
        self.verb = verbose
        # ---
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """
        Return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information
        """
        return {'ReferenceStructure': {'shell_width': self.shell_width,
                                       'r_max': self.r_max,
                                       'algorithm': self.algorithm,
                                       'topology_file': self.topology_file,
                                       'selection': self.selection,
                                       'distance': self.distance}}

    def _process_frame(self, frm_in):
        frm_out = copy.deepcopy(frm_in)
        frm_out.del_data(base.loc_coordinates)
        for spec_id in frm_in.get_keys(base.loc_coordinates):
            coord_in = frm_in.get_data(base.loc_coordinates + '/' + spec_id)
            if (self.shell_width > 0.0):
                # --- select core particles
                indices = librefstruct.selectCore(self.atoms.positions, coord_in,
                                                  self.distance, self.shell_width)
                coord_out = coord_in[indices]
                frm_out.put_data(base.loc_coordinates + '/' + spec_id,
                                 coord_out)
                # --- select shell particles
                indices = librefstruct.selectShell(self.atoms.positions, coord_in,
                                                   self.distance, self.shell_width)
                coord_out = coord_in[indices]
                frm_out.put_data(base.loc_coordinates + '/' + spec_id + '.s',
                                 coord_out)
            else:
                indices = librefstruct.selectBody(self.atoms.positions,
                                                  coord_in,
                                                  R=self.distance)
                coord_out = coord_in[indices]
                frm_out.put_data(base.loc_coordinates + '/' + spec_id,
                                 coord_out)
        frm_out.i = frm_in.i
        frm_out.put_data('log', frm_in.get_data('log'))
        frm_out.put_meta(self.get_meta())
        return frm_out

    def next(self):
        for frm_in in self.src.next():
            if frm_in is not None:
                assert isinstance(frm_in, base.Container)
                frm_out = self._process_frame(frm_in)
                if self.verb:
                    print "ReferenceStructure.next() :", frm_out.i
                yield frm_out
            else:
                yield None


class MultiReferenceStructure(ReferenceStructure):
    """
    A filter that selects particles within a volume defined by a reference
    structure from a generator returning base.Container with coordinate data.

    The maximum distance r_max is read from the parameter file. For each frame,
    the maximum distance is calculated.  If it is larger than the distance given
    by r_max, then r_max is set to the actual value.
    """
    _depends = []
    _conflicts = []

    def __init__(self,
                 topology_file=None,  # reference topology
                 trajectory_file=None,
                 selection='all',
                 distance=10,  # distance from reference structure
                 r_max=-1,
                 shell_width=-1,
                 algorithm="brute_force",
                 source=-1,
                 verbose=False):
        self.topology_file = topology_file
        self.trajectory_file = trajectory_file
        self.selection = selection
        self.distance = distance
        self.shell_width = shell_width
        self.r_max = r_max
        self.algorithm = algorithm
        librefstruct.set_algorithm(algorithm)
        # ---
        self.universe = mda.Universe(topology_file, trajectory_file)
        self.atoms = self.universe.atoms.select_atoms(selection)
        # ---
        self.src = source
        self.verb = verbose
        # ---
        self._depends.extend(ReferenceStructure._depends)
        self._conflicts.extend(ReferenceStructure._conflicts)

    def get_meta(self):
        """
        Return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information
        """
        return {'MultiReferenceStructure': {'shell_width': self.shell_width,
                                            'r_max': self.r_max,
                                            'algorithm': self.algorithm,
                                            'topology_file': self.topology_file,
                                            'trajectory_file': self.trajectory_file,
                                            'selection': self.selection,
                                            'distance': self.distance}}

    def next(self):
        for frm_in in self.src.next():
            if frm_in is not None:
                assert isinstance(frm_in, base.Container)
                # go to new frame to update self.atoms
                try:
                    # Translate 1-based to 0-based indexing!
                    # TODO: carefully check if this is globally consistent throughout the code!!!
                    frm_idx_0 = frm_in.i - 1
                    # assert will likely fail at the first frame if sth is wrong with the indexing
                    assert(frm_idx_0 >= 0)
                    self.universe.trajectory[frm_idx_0]
                except:
                    raise RuntimeError("Frame %d not available in reference trajectory" % frm_in.i)
                # if self.qDetermineRMax==True:
                d_max = librefstruct.maxInnerDistance(self.atoms.positions)
                d_max += 3. * self.distance
                if d_max > self.r_max:
                    self.r_max = d_max
                frm_out = self._process_frame(frm_in)
                if self.verb:
                    print "MultiReferenceStructure.next() :", frm_out.i
            else:
                frm_out = None
            yield frm_out
