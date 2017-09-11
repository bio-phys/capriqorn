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


"""Wrapper for the example generators.
"""


def configure_cli(subparsers):
    """Attach a parser (specifying command name and flags) to the argparse subparsers object."""
    parser = subparsers.add_parser('example', help='generate example parameter file')
    parser.add_argument('--preproc', help='write preprocessor parameter file', action='store_true')
    parser.add_argument('--histo', help='write histogram parameter file', action='store_true')
    parser.add_argument('--postproc', help='write postprocessor parameter file', action='store_true')
    parser.add_argument('--expert', help='show expert parameters', action='store_true')
    parser.set_defaults(func=main)


def main(pargs):
    from . import preprocessor_example
    from . import postprocessor_example
    from cadishi.exe import histograms_example

    if (not pargs.preproc) and (not pargs.histo) and (not pargs.postproc):
        preprocessor_example.main(pargs)
        histograms_example.main(pargs)
        postprocessor_example.main(pargs)
    else:
        if (pargs.preproc):
            preprocessor_example.main(pargs)
        if (pargs.histo):
            histograms_example.main(pargs)
        if (pargs.postproc):
            postprocessor_example.main(pargs)
