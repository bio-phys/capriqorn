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


"""
Capriqorn data postprocessor.

Reads input from a JSON file, creates and runs the pipeline.
"""


from __future__ import print_function
import os
import sys
import json
import argparse
from cadishi import util
from ..lib import pipeutil
from .. import postproc
from .. import version


def configure_cli(subparsers):
    """Attach a parser (specifying command name and flags) to the argparse subparsers object."""
    parser = subparsers.add_parser('postproc', help='run postprocessor')
    parser.add_argument('input', nargs=argparse.REMAINDER,
                        help='postprocessor parameter file (optional)', metavar='postprocessor.yaml')
    parser.set_defaults(func=main)


@util.timefunc
# @util.do_cprofile
def main(argparse_args):
    print(util.SEP)

    if (argparse_args.input):
        parameter_file = argparse_args.input[0]
    else:
        if util.have_yaml:
            parameter_file = 'postprocessor.yaml'
        else:
            parameter_file = 'postprocessor.json'

    if not os.path.exists(parameter_file):
        print(" Could not find postprocessor input file <" + parameter_file + ">.")
        print(" Run `" + util.get_executable_name() + " example --postproc` to generate an example input file.")
        print(util.SEP)
        exit(1)

    try:
        pipeline_meta = util.load_parameter_file(parameter_file)
    except:
        print(" Error: Could not read input file <" + parameter_file + ">.")
        sys.exit(1)

    print(version.get_printable_version_string())
    print(util.SEP)
    print(" Setting up pipeline based on <" + parameter_file + ">.")

    pipeline_module = "capriqorn.postproc"

    pipeutil.run_pipeline(pipeline_meta, pipeline_module)

    print(" ... done.")
    print(util.SEP)
