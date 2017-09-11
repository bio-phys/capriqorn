# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Some functions and classed used by the Capriqorn test suite.
"""


import os
from os.path import join as pjoin, isfile, dirname
import pytest
import copy
import cadishi.base as base
from capriqorn.preproc import io


class TestDataDir(object):
    """
    Simple class to access a directory with test data
    """

    def __init__(self, folder, data_folder):
        self.folder = pjoin(folder, data_folder)

    def __getitem__(self, file):
        data_filename = pjoin(self.folder, file)
        if isfile(data_filename):
            return data_filename
        else:
            raise RuntimeError("no file '{}' found".format(file))


@pytest.fixture
def data(request):
    """access test directory in a pytest. This works independent of where tests are
    started"""
    return TestDataDir(request.fspath.dirname, 'data')


@pytest.fixture
def reader():
    """
    provide a default reader object that can be used for further tests
    """
    data = TestDataDir(pjoin(dirname(__file__), 'tests'), 'data')
    reader = io.MDReader(pdb_file=data["protein.pdb.gz"],
                         trajectory_file=data["protein.crdbox.gz"],
                         alias_file=data["alias.dat"])
    return reader


class FrameCounter(base.Filter):
    def __init__(self, source=-1):
        self.src = source
        self.count = 0
        self.frames = []

    def get_meta(self):
        """Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information.
        """
        meta = {}
        label = 'FrameCounter'
        param = {}
        meta[label] = param
        return meta

    def next(self):
        for frm in self.src.next():
            self.count += 1
            self.frames.append(frm.i)
            yield frm


class KeepLastFrame(base.Filter):
    def __init__(self, source=-1):
        self.src = source
        self.last_frame = None

    def get_meta(self):
        """Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information.
        """
        meta = {}
        label = 'KeepLastFrame'
        param = {}
        meta[label] = param
        return meta

    def next(self):
        for frm in self.src.next():
            yield frm
        self.last_frame = copy.deepcopy(frm)


# --- legacy code below ---


def get_test_data_file_path(test_data_file_name=''):
    """Try to locate the test case that comes with capriqorn.

    Returns the full path to the test data directory including a trailing slash,
    if 'test_data_file_name' is given, the full path to the file is returned,
    or None in case the directory and/or file does not exist.
    """
    # get path to the current Python file
    file_path = os.path.dirname(os.path.abspath(__file__))
    # construct relative test data file path
    testcase_path = os.path.abspath(file_path + "/tests/data/" + test_data_file_name)
    if (os.path.isdir(testcase_path)):
        return testcase_path + "/"
    if (os.path.isfile(testcase_path)):
        return testcase_path
    else:
        return None
