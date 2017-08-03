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
import multiprocessing as mp
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

    (n_parallel, n_workers_per_segment) = pipeutil.get_parallel_configuration(pipeline_meta)

    if (n_parallel <= 0):
        pipeline = pipeutil.create(pipeline_meta, pipeline_module)
        pipeutil.check_dependencies(pipeline, pipeline_module)
        pipeutil.check_conflicts(pipeline, pipeline_module)
        print(" Running sequential pipeline ...", end='')
        sys.stdout.flush()
        pipeline[-1].dump()
    else:
        # counting: reader, writer, parallel workers, workers between parallel regions
        n_workers = sum(n_workers_per_segment)
        print(" Running parallel pipeline with " + str(n_workers) + " worker processes in total...")
        # split pipeline description into per-process parts, obtain queue handles
        meta_segments = pipeutil.get_meta_segments(pipeline_meta)

        # launch child processes to work on the segmented pipeline
        enumerated_segments = [pair for pair in enumerate(meta_segments)]
        last, segment = enumerated_segments[-1]
        mp_pool = []
        for i, segment in enumerated_segments:
            if (i == last):
                # run the last pipeline segment on the present process
                worker_id = 'segment_' + str(i) + '_worker_main'
                pipeline = pipeutil.create(segment, pipeline_module, worker_id)
            else:
                # run any previous pipeline egments on child processes
                for j in range(n_workers_per_segment[i]):
                    worker_id = 'segment_' + str(i) + '_worker_' + str(j)
                    mp_worker = mp.Process(target=pipeutil.partial_pipeline_worker,
                                           args=(segment, pipeline_module, worker_id))
                    mp_pool.append(mp_worker)

        for mp_worker in mp_pool:
            mp_worker.start()

        sys.stdout.flush()

        # launch the last segment of the pipeline
        pipeline[-1].dump()

        # all the child processes need to be finished until now, nevertheless we join() them
        for mp_worker in mp_pool:
            mp_worker.join()

    print(" done.")
    print(util.SEP)
