"""Capriqorn filter library <testing.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
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
                         traj_file=data["protein.crdbox.gz"],
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


def testcase():
    """Try to locate the test case that comes with capriqorn.
    
    Returns the full path to the testcase including a trailing slash, or None.
    """
    file_path = os.path.dirname(os.path.abspath(__file__))
    testcase_path = os.path.abspath(file_path + "/tests/data")
    if (os.path.isdir(testcase_path)):
        return testcase_path + "/"
    else:
        return None
