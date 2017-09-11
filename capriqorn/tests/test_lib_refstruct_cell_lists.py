#!/usr/bin/env python2.7
# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


import numpy as np
import MDAnalysis as mda
import copy
import sys
import time
from scipy.spatial.distance import cdist

from capriqorn.lib import refstruct
from capriqorn.testing import get_test_data_file_path

write_xyz = False


def test_refstuct_cell_list():
    # cut out distance with respect to reference structure
    distance = 10.
    topology_file = {}
    selection_strg = {}
    topology_file['lsz'] = get_test_data_file_path("lsz.pdb.gz")  # "./data/lsz.pdb"
    selection_strg['lsz'] = 'name C* and not name CL'

    topology_file['F1'] = get_test_data_file_path("F1ATPase.pdb.gz")  # "./data/F1ATPase.pdb"
    selection_strg['F1'] = 'name C* and not name Cl*'

    system = 'lsz'
    system = 'F1'

    # read in data and select full and reference structure
    universe = mda.Universe(topology_file[system])

    # selecting full structure
    selection = 'all'
    atoms = universe.atoms.select_atoms(selection)
    positions = atoms.positions

    # selecting reference structure, i.e., all carbons for a protein (CL are chloride ions)
    ref_selection = selection_strg[system]
    ref_atoms = universe.atoms.select_atoms(ref_selection)
    ref_positions = ref_atoms.positions

    print " number of particles of full system: ", positions.shape[0]
    print " number of particles of reference system:", ref_positions.shape[0]

    # # Cell-list method (step by step)

    # calling helper function
    neighbours = refstruct.get_neighbours()
    print " relative locations of neighbour cells:", neighbours

    # determine to which cell each particle belongs
    # for the full structure
    cell_indices = refstruct.get_cell_indices(positions, distance)
    cell_indices_strings = refstruct.get_cell_strings(cell_indices)
    uniq_cell_indices_strings = set(cell_indices_strings)
    print " number of cells for full structure =", len(uniq_cell_indices_strings)

    # for the reference structure
    ref_cell_indices = refstruct.get_cell_indices(ref_positions, distance)
    ref_cell_indices_strings = refstruct.get_cell_strings(ref_cell_indices)
    ref_uniq_cell_indices_strings = set(ref_cell_indices_strings)
    print " number of cells for ref. structure =", len(ref_uniq_cell_indices_strings)

    # collecting all particle indices belonging to one cell in a single dictionary entry
    particle_indices = refstruct.get_particle_indices(cell_indices_strings, uniq_cell_indices_strings)
    ref_particle_indices = refstruct.get_particle_indices(ref_cell_indices_strings, ref_uniq_cell_indices_strings)

    # collecting all particle indices within a cell and its neighbours in a single dictionary entry
    particle_indices_within_neighbours = refstruct.get_particle_indices_within_neighbours(
        ref_particle_indices, particle_indices, cell_indices, neighbours)

    print " approximate number of particles within central cell and its neighbours: ", distance**3 * 27 * 0.1
    print " number of particles within central cells and neighbours"
    print " key of central cell | number of particles"
    for k in particle_indices_within_neighbours:
        print k, len(particle_indices_within_neighbours[k])

    # Determine indices of particles in observation volume using cell lists.
    i_out, num_distances_calc = refstruct.get_observation_volume_particle_indices(ref_positions, positions, ref_particle_indices,
                                                                                  particle_indices_within_neighbours, distance)
    print " number of distances calculated = %3.2e" % num_distances_calc
    all2all_num_distance_calc = len(positions) * len(ref_positions)
    print " relative to all-to-all: %3.2f" % (num_distances_calc / float(all2all_num_distance_calc))
    print

    # # Brute force method (highly optimized by Klaus)

    # For comparison, without cell list. Method scales like [# particles in full system]x[#particles in reference system])
    t0 = time.time()
    mask = refstruct.queryDistance(np.asarray(positions, dtype=np.float64),
                                   np.asarray(ref_positions, dtype=np.float64), distance)
    t1 = time.time()

    print "### c_refstruct.queryDistance() : dt =", str(t1 - t0)

    n_elem_mask = np.sum(mask)

    # # Cell-list method (all steps)

    t0 = time.time()
    i_out, num_distances_calc = refstruct.cutout_using_cell_lists(positions, ref_positions, distance)
    t1 = time.time()
    print " number of distances calculated = %3.2e" % num_distances_calc
    print " relative to all-to-all: %3.2f" % (num_distances_calc / float(all2all_num_distance_calc))
    print "### cutout_using_cell_lists() : dt =", str(t1 - t0)

    # check if we see the same number of particles
    num_particles = len(i_out)
    assert(n_elem_mask == num_particles)
    print " number of particles in observation volume:", num_particles

    # Write observation volume to xyz for visualization with vmd.
    if write_xyz:
        fp = open("out.%s.xyz" % system, 'w')
        fp.write("%d\n" % num_particles)
        fp.write("cell_list.ipynb\n")
        coords = atoms.positions[i_out]
        names = atoms.names[i_out]
        for i in range(num_particles):
            fp.write("%s " % names[i] + "%6.3f %6.3f %6.3f\n" % tuple(coords[i]))
        fp.close()


if __name__ == "__main__":
    test_refstuct_cell_list()
