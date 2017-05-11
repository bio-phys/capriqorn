"""capriqorn filter library <preproc_filter_refstruct.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""
import MDAnalysis as mda
import numpy as np
import copy
from cadishi import base
from scipy.spatial.distance import cdist
# use Cython-accelerated functions, if possible
try:
    from capriqorn.kernel import c_refstruct
    have_c_refstruct = True
except:
    have_c_refstruct = False
    print(" Note: capriqorn.preproc.filter.refstruct: could not import c_refstruct")


def queryDistance(xyz, ref, R):
    """Lightweight wrapper of the queryDistance function."""
    # the cython kernel needs double precision input
    xyz = np.asanyarray(xyz, dtype=np.float64)
    ref = np.asanyarray(ref, dtype=np.float64)
    if have_c_refstruct:
        return c_refstruct.queryDistance(xyz, ref, R)
    else:
        return queryDistance_opt(xyz, ref, R)

def queryDistance_opt(xyz, ref, R):
    """Check which atoms in xyz lie within a radius R of any reference
    atom.

    Improved implementation in terms of memory and speed.

    Parameters
    ----------
    xyz : array_like (n_atoms, n_dim)
        atoms positions
    ref : array_like (n_atoms, n_dim)
        Reference atoms positions
    R : float
        distance to any atoms

    Returns
    -------
    query : ndarray (n_atoms)
        boolean array showing which particle are close to ref
    """
    xyz = np.asanyarray(xyz)
    ref = np.asanyarray(ref)
    mask = np.zeros(xyz.shape[0], dtype=bool)
    for i, a in enumerate(xyz):
        for b in ref:
            if (np.less(np.linalg.norm(a - b), R)):
                mask[i] = True
                break
    return mask

def queryDistance_legacy(xyz, ref, R):
    """Check which atoms in xyz lie within a radius R of any reference
    atom.

    Original implementation, expensive in terms of memory and CPU time
    at large problem sizes.

    Parameters
    ----------
    xyz : array_like (n_atoms, n_dim)
        atoms positions
    ref : array_like (n_atoms, n_dim)
        Reference atoms positions
    R : float
        distance to any atoms

    Returns
    -------
    query : ndarray (n_atoms)
        boolean array showing which particle are close to ref
    """
    xyz = np.asanyarray(xyz)
    ref = np.asanyarray(ref)
    return (cdist(xyz, ref) < R).sum(1).astype(bool)


def selectBody(ref_coords, coords, R):
    """
    Return indices of the particles within the sphere of radius R.

    Parameters
    ----------
    ref_coords : array_like (n_atoms, n_dim)
        Reference atoms positions
    coords : array_like (n_atoms, n_dim)
        atoms positions
    R : float
        distance to any atoms

    Returns
    -------
    array
        particle indices within reference
    """
    return np.where(queryDistance(coords, ref_coords, R))


def selectShell(ref_coords, coords, R, sw):
    """
    Return indices of the particles within the spherical shell of
    inner radius (R-sw) and outer radius R, ie the shell.

    Parameters
    ----------
    ref_coords : array_like (n_atoms, n_dim)
        Reference atoms positions
    coords : array_like (n_atoms, n_dim)
        atoms positions
    R : float
        distance to any atoms

    Returns
    -------
    array
        particle indices within shell
    """
    if R < sw:
        raise RuntimeError("selection radius smaller then shell width")
    body_query = queryDistance(coords, ref_coords, R=R)
    core_query = queryDistance(coords, ref_coords, R=R - sw)
    query = np.logical_xor(body_query, core_query)
    return np.where(query)


def selectCore(ref_coords, coords, R, sw):
    """
    Return indices of the particles within the sphere of
    radius (R-sw), ie the core.

    Parameters
    ----------
    ref_coords : array_like (n_atoms, n_dim)
        Reference atoms positions
    coords : array_like (n_atoms, n_dim)
        atoms positions
    R : float
        distance to any atoms

    Returns
    -------
    array
        particle indices the inner shell
    """
    if R < sw:
        raise RuntimeError("selection radius smaller then shell width")
    return selectBody(ref_coords, coords, R=R - sw)


def maxInnerDistance(xyz):
    """max distance between atoms in ``xyz``

    Parameters
    ----------
    xyz : array_like
        array of atoms positions

    Returns
    -------
    float
        maximal distance
    """
    return cdist(xyz, xyz).max()


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
                 distance=None,  # distance from reference structure
                 shell_width=-1,
                 source=-1,
                 verbose=False):
        self.topology_file = topology_file
        self.selection = selection
        self.distance = distance
        self.shell_width = shell_width
        # ---
        universe = mda.Universe(topology_file)
        self.atoms = universe.atoms.select_atoms(selection)
        # --- calculate r_max from longest distance in reference structure
        d_max = maxInnerDistance(self.atoms.positions)
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
                indices = selectCore(self.atoms.positions, coord_in,
                                     self.distance, self.shell_width)
                coord_out = coord_in[indices]
                frm_out.put_data(base.loc_coordinates + '/' + spec_id,
                                 coord_out)
                # --- select shell particles
                indices = selectShell(self.atoms.positions, coord_in,
                                      self.distance, self.shell_width)
                coord_out = coord_in[indices]
                frm_out.put_data(base.loc_coordinates + '/' + spec_id + '.s',
                                 coord_out)
            else:
                indices = selectBody(self.atoms.positions,
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
            assert isinstance(frm_in, base.Container)
            frm_out = self._process_frame(frm_in)
            if self.verb:
                print "ReferenceStructure.next() :", frm_out.i
            yield frm_out


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
                 distance=None,  # distance from reference structure
                 r_max=-1,
                 shell_width=-1,
                 source=-1,
                 verbose=False):
        self.topology_file = topology_file
        self.trajectory_file = trajectory_file
        self.selection = selection
        self.distance = distance
        self.shell_width = shell_width
        self.r_max = r_max
        # ---
        self.universe = mda.Universe(topology_file, trajectory_file)
        self.atoms = self.universe.atoms.select_atoms(selection)
        # ---
        self.src = source
        self.verb = verbose
        # ---
        #self._depends.extend(super(base.ReferenceStructure, self)._depends)
        #self._conflicts.extend(super(base.ReferenceStructure, self)._conflicts)

    def get_meta(self):
        """
        Return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information
        """
        return {'MultiReferenceStructure': {'shell_width': self.shell_width,
                                            'r_max': self.r_max,
                                            'topology_file': self.topology_file,
                                            'trajectory_file': self.trajectory_file,
                                            'selection': self.selection,
                                            'distance': self.distance}}

    def next(self):
        for frm_in in self.src.next():
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
            d_max = maxInnerDistance(self.atoms.positions)
            d_max += 3. * self.distance
            if d_max > self.r_max:
                self.r_max = d_max
            frm_out = self._process_frame(frm_in)
            if self.verb:
                print "MultiReferenceStructure.next() :", frm_out.i
            yield frm_out
