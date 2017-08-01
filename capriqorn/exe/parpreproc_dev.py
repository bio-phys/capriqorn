#!/usr/bin/env python2.7

"""
Capriqorn data preprocessor.

Reads input from a JSON file, creates and runs the pipeline.

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
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
    parser = subparsers.add_parser('pardev', help='develop parallel preprocessor')
    parser.add_argument('input', nargs=argparse.REMAINDER, help='preprocessor parameter file (optional)', metavar='preprocessor.yaml')
    parser.set_defaults(func=main)


# @util.do_cprofile
@util.timefunc
def main(argparse_args):
    print(util.SEP)

    if (argparse_args.input):
        parameter_file = argparse_args.input[0]
    else:
        if util.have_yaml:
            parameter_file = 'preprocessor.yaml'
        else:
            parameter_file = 'preprocessor.json'

    if not os.path.exists(parameter_file):
        print(" Could not find preprocessor input file <" + parameter_file + ">.")
        print(" Run `" + util.get_executable_name() + " preproc-example` to generate an example input file.")
        print(util.SEP)
        sys.exit(1)

    try:
        pipeline_meta = util.load_parameter_file(parameter_file)
    except:
        print(" Error: Could not read input file <" + parameter_file + ">.")
        sys.exit(1)

    print(version.get_printable_version_string())
    print(util.SEP)
    print(" Setting up pipeline based on <" + parameter_file + ">.")

    pipeline_module = "capriqorn.preproc"

    (n_parallel, n_parallel_workers) = pipeutil.get_parallel_configuration(pipeline_meta)

    if (n_parallel <= 0):
        pipeline = pipeutil.create(pipeline_meta, pipeline_module)
        pipeutil.check_dependencies(pipeline, pipeline_module)
        pipeutil.check_conflicts(pipeline, pipeline_module)
        print(" Running sequential pipeline ...", end='')
        sys.stdout.flush()
        pipeline[-1].dump()
    else:
        # counting: reader, writer, parallel workers, workers between parallel regions
        n_workers = 2 + n_parallel_workers + (n_parallel - 1)
        print(" Running parallel pipeline with " + str(n_workers) + " worker processes in total...", end='')
        q_pairs = pipeutil.prepare_mp_queues(n_parallel)

    print(" done.")
    print(util.SEP)
