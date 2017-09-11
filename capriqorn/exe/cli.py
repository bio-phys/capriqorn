# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
# 
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN 
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

#!/usr/bin/env python2.7

"""Capriqorn main executable.  Uses argparse to call further scripts.
"""
# This file is part of the Capriqorn package.  See README.rst,
# LICENSE.txt, and the documentation for details.

__author__ = "Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2016 Klaus Reuter"
__license__ = "license_tba"


import sys
import argparse
from . import preprocessor
from . import postprocessor
from . import example
from . import compare
from cadishi.exe import histograms
from cadishi.exe import merge
from cadishi.exe import unpack
from .. import version

version_string = version.get_printable_version_string()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', help='print version information',
                        action='version', version=version_string)
    subparsers = parser.add_subparsers(help='Commands')
    preprocessor.configure_cli(subparsers)
    histograms.configure_cli(subparsers)
    postprocessor.configure_cli(subparsers)
    example.configure_cli(subparsers)
    merge.configure_cli(subparsers)
    unpack.configure_cli(subparsers)
    # "secret" command
    if ('compare' in '\t'.join(sys.argv)):
        compare.configure_cli(subparsers)
    # ---
    return parser.parse_args()


def main():
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
