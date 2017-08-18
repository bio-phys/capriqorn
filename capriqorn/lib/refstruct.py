"""Library for the Capriqorn reference structure filter.

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""

import numpy as np
from scipy.spatial.distance import cdist
# use Cython-accelerated functions, if possible
try:
    from capriqorn.kernel import c_refstruct
    have_c_refstruct = True
except:
    have_c_refstruct = False
    print(" Note: capriqorn.lib.refstruct: could not import c_refstruct")


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
