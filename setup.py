# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
# 
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN 
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

# ez_setup attempts to download setuptools in case it is not available
# import ez_setup
# ez_setup.use_setuptools()
from __future__ import print_function
from setuptools import setup, Extension, Command
import os
import sys
import glob
import numpy
import platform


# --- optionally, useful during development, re-generate C code from Cython code
cy_flag = "--cython"
if cy_flag in sys.argv:
    do_cython = True
    sys.argv.remove(cy_flag)
else:
    do_cython = False
if do_cython:
    from Cython.Build import cythonize
    print("Re-generating C code for extensions from Cython sources ...")


def get_version_string():
    ver = {}
    with open("./capriqorn/version.py") as fp:
        exec(fp.read(), ver)
    return ver['get_version_string']()


def on_mac():
    """Check if we're running on a Mac.  Returns True or False."""
    if "Darwin" in platform.system():
        return True
    else:
        return False


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    # https://stackoverflow.com/questions/3779915/why-does-python-setup-py-sdist-create-unwanted-project-egg-info-in-project-r
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('rm -vrf ./*.so')
        os.system('rm -vrf ./build')
        os.system('rm -vrf ./dist')
        os.system('rm -vrf ./capriqorn.egg-info')
        os.system("find capriqorn -name '*.pyc' -delete -print")
        os.system("find capriqorn -name '*.so' -delete -print")


def find_in_path(filenames):
    """Find file on system path."""
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52224
    from os.path import exists, join, abspath
    from os import pathsep, environ
    search_path = environ["PATH"]
    paths = search_path.split(pathsep)
    for path in paths:
        for filename in filenames:
            if exists(join(path, filename)):
                return abspath(join(path, filename))


# compilation of the Cython extension
cc_flags = ['-O3']
if (find_in_path(['gcc']) is not None):
    # let us assume that gcc will be used
    cc_flags += ['-ffast-math']
    # cc_flags += ['-msse4.2']  # runs well on any reasonably modern system
    # cc_flags += ['-mavx']  # AVX, found to be slower than SSE 4.2
    # cc_flags += ['-march=native']  # non portable, not clear what gcc is doing
    cc_flags += ['-mtune=native']  # portable
    # if not on_mac():
    #     cc_flags += ['-fopenmp']
else:
    pass


# Obtain the numpy include directory.  This logic works across numpy versions.
try:
    numpy_include = numpy.get_include()
except AttributeError:
    numpy_include = numpy.get_numpy_include()


# --- Cython extensions to accelerate critical code
c_pddf_basename = 'capriqorn/kernel/c_pddf'
if do_cython:
    cythonize([c_pddf_basename + '.pyx'])
c_pddf = Extension(c_pddf_basename.replace('/', '.'),
                   sources=[c_pddf_basename + '.c'],
                   include_dirs=[numpy_include],
                   extra_compile_args=cc_flags,
                   extra_link_args=cc_flags)

c_virtual_basename = 'capriqorn/kernel/c_virtual_particles'
if do_cython:
    cythonize([c_virtual_basename + '.pyx'])
c_virtual_particles = Extension(c_virtual_basename.replace('/', '.'),
                                sources=[c_virtual_basename + '.c'],
                                include_dirs=[numpy_include],
                                extra_compile_args=cc_flags,
                                extra_link_args=cc_flags)

c_refstruct_basename = 'capriqorn/kernel/c_refstruct'
if do_cython:
    cythonize([c_refstruct_basename + '.pyx'])
c_refstruct = Extension(c_refstruct_basename.replace('/', '.'),
                        sources=[c_refstruct_basename + '.c'],
                        include_dirs=[numpy_include],
                        extra_compile_args=cc_flags,
                        extra_link_args=cc_flags)
# ---


entry_points = {
    'console_scripts': ['capriq=capriqorn.exe.cli:main']
}


# copy the test case to the same relative location in the installation directory
data_files = [('capriqorn/tests/data', glob.glob('capriqorn/tests/data/*')),
              ('capriqorn/data', glob.glob('capriqorn/data/*'))]


setup(name='capriqorn',
      version=get_version_string(),
      description='RDF calculation framework',
      author='Juergen Koefinger, Klaus Reuter',
      author_email='juergen.koefinger@biophys.mpg.de, khr@mpcdf.mpg.de',
      packages=['capriqorn',
                'capriqorn.exe',
                'capriqorn.kernel',
                'capriqorn.lib',
                'capriqorn.legacy',
                'capriqorn.preproc',
                'capriqorn.preproc.filter',
                'capriqorn.preproc.io',
                'capriqorn.postproc',
                'capriqorn.postproc.filter',
                'capriqorn.postproc.io',
                'capriqorn.tests'],
      install_requires=['numpy', 'scipy', 'h5py', 'pyyaml', 'six',
                        'cadishi', 'MDAnalysis>=0.14.0'],
      ext_modules=[c_pddf, c_virtual_particles, c_refstruct],
      # cmdclass={'build_ext': Cython.Distutils.build_ext, 'clean': CleanCommand},
      cmdclass={'clean': CleanCommand},
      entry_points=entry_points,
      data_files=data_files,
      zip_safe=False)
