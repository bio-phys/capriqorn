# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Capriqorn reader for legacy distHisto files.
"""

import os
import numpy as np
import json
import glob
from six.moves import range

from cadishi import base
from cadishi import util


class distHistoReader(base.Reader):
    """
    Reader for the original output format of histograms.py.
    """
    _depends = []
    _conflicts = []

    def __init__(self, directory='histograms_output',
                 list_file='distHisto.list',
                 header_file='header.dat',
                 first=None, last=None, step=1, verbose=False):
        self.count = 0
        self.directory = directory
        self.list_file = list_file
        self.file_list = []
        self.header_file = header_file
        self.header = []
        self.nr_part_header = []
        self.nr_part_table = None
        self.first = first
        self.last = last
        self.step = step
        self.verb = verbose
        self.pipeline_log = []
        # ---
        self._depends.extend(super(base.Reader, self)._depends)
        self._conflicts.extend(super(base.Reader, self)._conflicts)
        # --- check input configuration, create list of input files
        assert (os.path.isdir(self.directory))
        filename = os.path.join(directory, list_file)
        assert (os.path.exists(filename))
        with open(filename) as fp:
            _file_list = [os.path.join(directory, line.strip()) for line in fp]
        # Remove elements from the file_list to handle first,last,step.
        # By convention (as is done in MD reader written by Juergen)
        # first and last are not list indices starting at 0 but rather
        # natural counting numbers starting from 1 (such as in FORTRAN).
        # None: We use a temporary array of 'good' indices to accomplish
        # this task because it is repeated below for the nrPart table.
        idx_selection = list(range(len(_file_list)))
        if self.last is not None:
            assert (self.last > 0)
            if (self.last > len(idx_selection)):
                self.last = len(idx_selection)
            else:
                del idx_selection[self.last:]
        if self.first is not None:
            assert (len(idx_selection) >= self.first)
            del idx_selection[:self.first - 1]
        if self.step is not None:
            assert (self.step > 0)
            _step_list = idx_selection[::self.step]
            idx_selection = _step_list
        # --- apply the selection on the file list
        self.file_list = [_file_list[i] for i in idx_selection]
        # --- check existence
        for filename in self.file_list:
            assert (os.path.exists(filename))
        # --- read species combinations from the header file
        filename = os.path.join(directory, header_file)
        assert (os.path.exists(filename))
        with open(filename, 'r') as fp:
            header_raw = fp.readline()
            header_lst = header_raw.split()
            assert (header_lst[0] == '#')
            self.header = header_lst
        # --- read preprocessor pipeline log information
        filename = os.path.join(directory, 'preprocessor_log.json')
        if os.path.exists(filename):
            with open(filename) as fp:
                self.pipeline_log.extend(json.load(fp))
        # --- read and append histograms log information
        filename = os.path.join(directory, 'histograms_log.json')
        if os.path.exists(filename):
            with open(filename) as fp:
                # put the histograms config data in a dict to be
                # in line with the rest of the pipeline information
                entry = {}
                key = 'histograms'
                val = json.load(fp)
                entry[key] = val
                self.pipeline_log.append(entry)
        # --- read the number-of-particles table into memory
        _nr_part_files = glob.glob(os.path.join(directory, 'nrPart*.dat'))
        if (len(_nr_part_files) == 1):
            filename = _nr_part_files[0]
            _nr_part_table = None
            with open(filename, 'r') as fp:
                _header_raw = fp.readline()
                _header_lst = _header_raw.split()
                assert (_header_lst[0] == '#')
                self.nr_part_header = _header_lst
                _nr_part_table = np.loadtxt(fp)
            assert (_nr_part_table.shape[1] == len(self.nr_part_header))
            self.nr_part_table = _nr_part_table[idx_selection, :]
            assert (self.nr_part_table.shape[0] == len(self.file_list))
        else:
            pass

    def get_meta(self):
        """
        return information on the present filter,
        ready to be added to a HistogramSet object's list of
        pipeline meta information
        """
        meta = {}
        label = 'distHistoReader'
        param = {'directory': self.directory, 'list_file': self.list_file,
                 'header_file': self.header_file,
                 'first': self.first, 'last': self.last, 'step': self.step}
        meta[label] = param
        return meta

    def __iter__(self):
        return self

    def __next__(self):
        """iterate through all the histogram sets and yield set by set"""
        if self.verb:
            print()
        for i in range(len(self.file_list)):
            hs = base.Container()
            # --- fill the hs.histograms dictionary
            filename = self.file_list[i]
            histograms = np.load(filename)
            (_n_bins, n_rows) = histograms.shape
            # the zeroth column of histograms contains the radial grid
            radii = histograms[:, 0]
            hs.put_data(base.loc_histograms + '/radii', radii)
            assert (n_rows == len(self.header))
            # the following columns contain the distance histograms
            for idx in range(1, n_rows):
                key = self.header[idx]
                val = histograms[:, idx]
                hs.put_data(base.loc_histograms + '/' + key, val)
            # --- fill the hs.particles dictionary ---
            # The use of a numpy array to hold a single value may seem like
            # a bit of an overkill, but when averaging over several
            # HistogramSets the array will hold the particle numbers of all
            # the frames that have contributed to the averaged set.
            for j in range(len(self.nr_part_header)):
                key = self.nr_part_header[j]
                val = np.array([self.nr_part_table[i, j]], dtype=np.int32)
                hs.put_data(base.loc_nr_particles + '/' + key, val)
            # ---
            val = self.pipeline_log + [self.get_meta()]
            hs.put_data('log', val)
            # ---
            self.count += 1
            hs.i = self.count
            # ---
            yield hs
            if self.verb:
                print("distHistoReader.next() : " + filename)


class distHistoWriter(base.Writer):
    """
    Writer for the original output format of histograms.py.
    """
    _depends = []
    _conflicts = []

    def __init__(self,
                 source=None,
                 directory='postprocessor_output',
                 list_file='distHisto.list',
                 histo_file_prefix='distHisto',
                 header_file='header.dat',
                 write_txt=False,
                 verbose=False):
        self.count = 0
        self.src = source
        if directory[-1] is not '/':
            directory += '/'
        self.directory = directory
        self.list_file = list_file
        self.histo_file_prefix = histo_file_prefix
        self.header_file = header_file
        self.write_txt = write_txt
        self.verb = verbose
        # create output directory, if necessary
        util.md(self.directory)
        # create and truncate "file list"-file
        filename = os.path.join(self.directory, self.list_file)
        with open(filename, 'w') as _fp:
            pass
        # ---
        self._depends.extend(super(base.Writer, self)._depends)
        self._conflicts.extend(super(base.Writer, self)._conflicts)

    def get_meta(self):
        """
        return information on the present filter,
        ready to be added to a HistogramSet object's list of
        pipeline meta information
        """
        meta = {}
        label = 'distHistoWriter'
        param = {'directory': self.directory, 'list_file': self.list_file,
                 'header_file': self.header_file}
        meta[label] = param
        return meta

    def dump(self):
        """save histogram sets"""
        header_str = ''
        nbin = 0
        ncol = 0
        for obj in next(self.src):
            if obj is not None:
                if (self.count == 0):
                    header_lst = sorted(obj.get_keys(base.loc_histograms,
                                                     skip_keys=['radii']))
                    header_lst.insert(0, '#')
                    header_str = ' '.join(header_lst)
                    #
                    filename = os.path.join(self.directory, self.header_file)
                    with open(filename, 'w') as fp:
                        fp.write(header_str + '\n')
                    nbin = len(obj.get_data(base.loc_histograms + '/radii'))
                    ncol = len(obj.get_keys(base.loc_histograms, skip_keys=['radii'])) + 1
                # build a 2D numpy array containing the radii and the histograms
                assert (nbin == len(obj.get_data(base.loc_histograms + '/radii')))
                assert (ncol == len(obj.get_keys(base.loc_histograms, skip_keys=['radii'])) + 1)
                histo_array = np.ndarray((nbin, ncol))
                histo_array[:, 0] = obj.get_data(base.loc_histograms + '/radii')[:]
                idx = 1
                for key in sorted(obj.get_keys(base.loc_histograms, skip_keys=['radii'])):
                    histo_array[:, idx] = obj.get_data(base.loc_histograms + '/' + key)
                    idx += 1
                # write histograms to numpy files
                filenum = str(obj.i)
                if self.write_txt:
                    filename = self.histo_file_prefix + '.' + filenum + '.dat'
                    fullname = os.path.join(self.directory, filename)
                    util.savetxtHeader(fullname, header_str, histo_array)
                filename = self.histo_file_prefix + '.' + filenum + '.npy'
                fullname = os.path.join(self.directory, filename)
                np.save(fullname, histo_array)
                del histo_array
                # finally, append .npy filename to the list file
                util.appendLineToFile(os.path.join(self.directory, self.list_file),
                                      filename)
                # ---
                if self.verb:
                    print("distHistoWriter.dump() : " + fullname)
                self.count += 1
