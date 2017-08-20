#!/usr/bin/env python2.7

import MDAnalysis as mda

pdbName = "./protein.pdb.gz"
#trajName = "./protein.xtc"
trajName = "./protein.crdbox.gz"

universe = mda.Universe(pdbName, trajName)
n_frames = len(universe.trajectory)

print "n_frames = ", n_frames

for ts in universe.trajectory:
    print ts.frame
