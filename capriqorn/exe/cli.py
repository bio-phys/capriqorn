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

version_string = "Capriqorn " + version.get_version_string()
try:
    from .. import githash
except:
    pass
else:
    version_string += " (git: " + githash.human_readable + ")"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', help='print version information',
                        action='version', version=version_string)
    subparsers = parser.add_subparsers(help='Commands')
    # ---
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
