"""capriqorn preprocessor IO, MD reader/writer

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""
import numpy as np
import MDAnalysis as mda
from six.moves import range

from cadishi import base
from cadishi import pbc

__author__ = "Juergen Koefinger, Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2016 Juergen Koefinger, Klaus Reuter"
__license__ = "license_tba"


class MDReader(base.Reader):
    """Trajectory reader, built upon MDAnalysis."""
    _depends = []
    _conflicts = []

    def __init__(self, pdb_file="protein.pdb", traj_file="protein.xtc", selection='all',
                 alias_file="alias.dat", first=1, last=None, step=1, verbose=False):
        """Constructor of the MDAnalysis-based MDReader.

        Parameters
        ----------
        pdb_file : string
            File name of PDB file.
        traj_file : string
            File name of trajectory {xtc,crdbox} file.
        alias_file : string
            File name of alias file.
        selection : string
            species selection
        first : optional[int]
            Number of first frame to be read, default is 1.
        last : optional[int]
            Number of last frame to be read, default is None, ie. all available.
        step : optional[int]
            Step widh, i.e. skip step-1 frames
        verbose : bool
            Print information on what the reader is currently doing.  Default is False.

        Returns
        -------
        None
            The function only initializes member variables and does not return anything.
        """
        self.verb = verbose
        self.first = first
        self.last = last
        self.step = step
        self.initialized = False  # flag that is set to True when self.init() is called
        # --- pdb file needed for atom species
        self.pdb_file = pdb_file
        # --- Amber crd trajectory file with box information
        self.traj_file = traj_file
        # --- alias.dat needed to assign element names to atom names in pdb
        self.alias_file = alias_file
        self.selection = selection
                # ---
        self._depends.extend(super(base.Reader, self)._depends)
        self._conflicts.extend(super(base.Reader, self)._conflicts)

    def init(self):
        """Initialization routine that does actually open files to read information.
        Was separated from __init__ during the development of <preprocessor.py>
        because no actual work should be done during the setup of the pipeline.
        """
        aliasDict = dict(np.genfromtxt(self.alias_file, dtype='S4'))
        if self.traj_file.endswith(('crdbox', 'crdbox.gz', 'crdbox.bz2')):
            self.universe = mda.Universe(self.pdb_file, self.traj_file, format='trj')
        else:
            self.universe = mda.Universe(self.pdb_file, self.traj_file)
        self.atoms = self.universe.select_atoms(self.selection)
        # ---
        self.nrPart = self.atoms.n_atoms
        self.elList = [aliasDict[self.atoms[i].name] for i in
                       range(self.nrPart)]
        self.elements = sorted(list(set(self.elList)))
        # ---
        self.nEl = len(self.elements)
        self.el2idx = dict(zip(self.elements, range(1, self.nEl + 1)))
        self.speciesList = np.array([self.el2idx[nam] for nam in self.elList],
                                    dtype=np.int32)
        # check the values of `first` and `last` against the frame numbers
        n_frames = self.universe.trajectory.n_frames
        if (self.first is None):
            self.first = 1
        if (self.first > n_frames):
            raise IndexError("First frame index exceeds the maximum number of frames.")
        if self.last is None:
            self.last = n_frames
        else:
            if (self.first > self.last):
                raise IndexError("First frame index exceeds the last frame index.")
        # forward the trajectory reader to the first relevant frame
        for i in range(1, self.first):
            self.universe.trajectory.next()
        # ---
        self.initialized = True

    def get_meta(self):
        """Return information on the reader, ready to be added to a frame
        object's list of pipeline meta information.
        """
        meta = {}
        label = 'MDReader'
        param = {'pdb_file': self.pdb_file, 'traj_file': self.traj_file,
                 'alias_file': self.alias_file,
                 'first': self.first, 'last': self.last, 'step': self.step}
        meta[label] = param
        return meta

    def next(self):
        """Generator that iterates through all the frames and yields
        frame by frame.
        """
        if not self.initialized:
            self.init()
        # counters to make self.last and self.step work
        i = self.first  # numbering relative to the original dataset
        raw_count = 0  # count the raw frames delivered by MDAnalysis
        for ts in self.universe.trajectory:
            if (i > self.last):
                break
            elif (raw_count % self.step == 0):
                coord = self.atoms.positions
                dimensions = self.universe.atoms.dimensions
                # --- separate coordinates by species and put them into the container
                frm = base.Container()
                for si in range(1, self.nEl + 1):
                    species_label = self.elements[si - 1]
                    species_coord = coord[np.where(self.speciesList == si)]
                    # we need to add the coordinates type-converted to 64 bit floats
                    frm.put_data(base.loc_coordinates + '/' + species_label,
                                 species_coord.astype(np.float64))
                frm.put_data(base.loc_dimensions, dimensions)
                frm.i = i
                frm.put_meta(self.get_meta())
                if self.verb:
                    print "MDReader.next() : ", frm.i
                yield frm
            # ---
            i = i + 1
            raw_count += 1
