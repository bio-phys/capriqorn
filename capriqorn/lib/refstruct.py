"""Library for the Capriqorn reference structure filter.

Includes naive particle cutout functions as well as more sophisticated ones
based on cell lists (by Juergen Koefinger).

The cell list implementation uses dictionaries (hashes). The number of particles
considered is given by the cutoff distance and approximately d^3*27, where d is
the cutout distance. d is usually 10 Angstrom.

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""

import numpy as np
import copy
import re
from scipy.spatial.distance import cdist
# use Cython-accelerated functions, if possible
try:
    from capriqorn.kernel import c_refstruct
    have_c_refstruct = True
except:
    have_c_refstruct = False
    print(" Note: capriqorn.lib.refstruct: could not import c_refstruct")


# cell lists are disabled for the moment due to non-optimum performance
q_cell_lists = False


def set_algorithm(algo):
    """Selects the algorithm to be used for the neighbour search.
    """
    global q_cell_lists
    if algo.lower().startswith("cell"):
        # print("   refstruct uses cell list for neighbor search")
        q_cell_lists = True
    else:
        # print("     (refstruct uses brute-force neighbor search)")
        q_cell_lists = False


def get_selection(xyz, ref, R):
    """Uppermost entry point to the reference structure selection functions.
    """
    if q_cell_lists:
        return cutout_using_cell_lists(xyz, ref, R, return_mask=True)
    else:
        return queryDistance(xyz, ref, R)


def queryDistance(xyz, ref, R):
    """Lightweight wrapper of the simple queryDistance functions.
    """
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
    return np.where(get_selection(coords, ref_coords, R))


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
    body_query = get_selection(coords, ref_coords, R=R)
    core_query = get_selection(coords, ref_coords, R=R - sw)
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


# --- cell list implementation by Juergen Koefinger below ---


def get_neighbours():
    """"Helper function. Initializes components of relative locations of neighbouring cells."""
    neighbours = []
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            for k in [-1, 0, 1]:
                if i != 0 or j != 0 or k != 0:
                    # print i,j,k
                    neighbours.append([i, j, k])
    neighbours = np.asarray(neighbours)
    return neighbours


def get_cell_indices(positions, distance):
    """
    Returns array of indices of cells to which particles with coordinates 'positions' belong to.

    Indices of a cell are given by three integer numbers, e.g., [1,0,-2] denotes a single cell.
    """
    return np.asarray(np.rint(positions / distance), dtype=np.int64)


def get_cell_strings(indices):
    """
    Converts lists of indices to strings for use as dictionary keys.

    Indices of a cell are given by three integer numbers, e.g., [1,0,-2] denotes a single cell,
    which results in the string "+1+0-2".
    """
    strings = []
    for inds in indices:
        strng = "%+d%+d%+d" % tuple(inds)
        strings.append(strng)
    return strings


def get_cell_index_from_string(string):
    """
    Converts a the string index representation to an integer triple representation.
    """
    tokens = re.split('(\d+)', string)
    index = []
    for i in xrange(3):
        index.append(int(tokens[2 * i] + tokens[2 * i + 1]))
    return np.asarray(index)


def get_neighbour_indices(indices, neighbours):
    """
    Returns cell indices of neighbouring cells of a given cell ('indices').

    Indices of a cell are given by three integer numbers, e.g., [1,0,-2] denotes a single cell.
    """
    neighbour_indices = indices[np.newaxis, :] + neighbours
    return neighbour_indices


def get_particle_indices(cell_indices_strings, uniq_cell_indices_strings):
    """
    Returns a dicionary of lists of particle indices.

    Each key corresponds to one cell the list contains the indices of the particles this cell.
    This indices are used to retrieve the coordinates from the corresponding array (e.g., 'positions').
    """
    particle_indices = {}
    for k in uniq_cell_indices_strings:
        particle_indices[k] = []
    for i, k in enumerate(cell_indices_strings):
        particle_indices[k].append(i)
    return particle_indices


def get_particle_indices_within_neighbours(ref_particle_indices, particle_indices, cell_indices, neighbours):
    """
    For each cell occupied by at least one particle of the reference structure (central cell),
    this function returns the indices of all particles of the full structure,
    which belong either to this central cell or its neighbours.
    """
    neigh_particle_indices = {}
    for k in ref_particle_indices:

        # add particle indices of the cells themselves
        if k in particle_indices:
            neigh_particle_indices[k] = copy.deepcopy(particle_indices[k])
        else:
            neigh_particle_indices[k] = []

        # get index of cell corresponding to key 'k' (cell indices of first particle in list)
        #ind = cell_indices[particle_indices[k][0]]
        # print "+++", k, ind
        ind = get_cell_index_from_string(k)

        # get indices of neighbour cells
        neighs = get_neighbour_indices(ind, neighbours)
        # get keys of neighbour cells
        neigh_particle_strings = get_cell_strings(neighs)
        # add indices of neighbour cells to list
        for kk in neigh_particle_strings:
            # Check if neighbouring cell is not empty. If so, we should raise an exception as
            # it indicates that the simulation box is too small for the currently used cutoff distance.
            if kk in particle_indices:
                neigh_particle_indices[k] = neigh_particle_indices[k] + particle_indices[kk]
    return neigh_particle_indices


def get_observation_volume_particle_indices(ref_positions, positions, ref_particle_indices,
                                            particle_indices_within_neighbours, distance, return_mask=False):
    """
    Returns indices (i_out) of particles within cutout distance of reference structure using cell lists,
    or the index-mask of these particles if return_mask is set to True.

    ref_postions: array of coordinates of particles of the reference structure
    postions:  array of coordinates of particles of the full system
    ref_particle_indices: Dictionary with keys corresponding to cells containing at least
        a single particle of the reference structure. Each entry contains a list of indices of
        all particles of the reference structure belonging to this cell.
    particle_indices_within_neighbours: Dictionary with same keys as 'ref_particle_indices' above.
        Contains lists of indices of all particles of full system belonging to central cell, refernced by key,
        and its neighbouring cells
    distance: cutout distance
    """
    distanceSqr = distance**2
    mask = np.zeros(len(positions), dtype=np.int64)
    num_distances_calc = 0
    for k in ref_particle_indices:
        ref = ref_positions[ref_particle_indices[k]]
        xyz = positions[particle_indices_within_neighbours[k]]
        tmp = queryDistance(np.asanyarray(xyz, dtype=np.float64), np.asanyarray(ref, dtype=np.float64), distance)
        num_distances_calc += len(ref) * len(xyz)
        dummy_indices = np.asanyarray(particle_indices_within_neighbours[k])[np.where(tmp)[0]]
        if len(dummy_indices) > 0:
            mask[dummy_indices] = 1
    # alternative implemenation using python loops
    #    for iref in ref_particle_indices[k]:
    #       for i in particle_indices_within_neighbours[k]:
    #            refx=ref_positions[iref]
    #            x=positions[i]
    #            dSqr=((refx-x)**2).sum()
    #            if dSqr<distanceSqr:
    #                mask[i]=1
    if return_mask:
        return mask
    else:
        i_out = np.where(mask == 1)[0]
        return i_out, num_distances_calc


def cutout_using_cell_lists(positions, ref_positions, distance, return_mask=False):
    """
    Returns indices of observation volume, which is defined by
    all particles with coordinates 'positions' within a distance 'distance' of the
    reference structure with particle coordinates 'ref_postions'.

    In case return_mask is True, only the particle index mask is returned.
    """
    # determine to which cell each particle belongs
    # for the full structure
    cell_indices = get_cell_indices(positions, distance)
    cell_indices_strings = get_cell_strings(cell_indices)
    uniq_cell_indices_strings = set(cell_indices_strings)
    # print " number of cells for full structure =", len(uniq_cell_indices_strings)
    # for the reference structure
    ref_cell_indices = get_cell_indices(ref_positions, distance)
    ref_cell_indices_strings = get_cell_strings(ref_cell_indices)
    ref_uniq_cell_indices_strings = set(ref_cell_indices_strings)
    # print " number of cells for ref. structure =", len(ref_uniq_cell_indices_strings)

    # collecting all particle indices belonging to one cell in a single dictionary entry
    particle_indices = get_particle_indices(cell_indices_strings, uniq_cell_indices_strings)
    ref_particle_indices = get_particle_indices(ref_cell_indices_strings, ref_uniq_cell_indices_strings)

    # calling helper function. 'neighbours' contains relative locations of neighbouring cells.
    neighbours = get_neighbours()

    # collecting all particle indices within a cell and its neighbours in a single dictionary entry
    particle_indices_within_neighbours = get_particle_indices_within_neighbours(
        ref_particle_indices, particle_indices, cell_indices, neighbours)

    # determine indices of particles in observation volume using cell lists.
    result = get_observation_volume_particle_indices(ref_positions, positions, ref_particle_indices,
                                                     particle_indices_within_neighbours, distance,
                                                     return_mask)
    return result


# --- end of cell lists implementation ---
