#!/usr/bin/env python2.7

"""
Capriqorn data preprocessor.

Reads input from a JSON file, creates and runs the pipeline.

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""

import cadishi.util


def configure_cli(subparsers):
    import argparse
    """Attach a parser (specifying command name and flags) to the argparse subparsers object."""
    parser = subparsers.add_parser('preproc', help='run preprocessor')
    parser.add_argument('input', nargs=argparse.REMAINDER, help='preprocessor parameter file (optional)', metavar='preprocessor.yaml')
    parser.set_defaults(func=main)


# @cadishi.util.do_cprofile
@cadishi.util.timefunc
def main(argparse_args):
    import os
    import sys
    import json
    from cadishi import util
    from .. import postproc
    from .. import version

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
        exit(1)

    pipeline_meta = []
    try:
        pipeline_meta = util.load_parameter_file(parameter_file)
    except:
        print " Error: Could not read input file <" + parameter_file + ">."
        exit(1)

    # --- set up pipeline from JSON meta information
    pipeline = []
    print " Capriqorn preprocessor (git: " + version + ")"
    print util.SEP
    print " Setting up pipeline based on <" + parameter_file + ">."
    for filter_meta in pipeline_meta:
        assert (len(filter_meta) == 1)
        label = ""
        parameters = {}
        for (label, parameters) in filter_meta.iteritems():
            # we leave the loop immediately since filter_meta must have only a single item
            break
        if 'active' in parameters:
            if (parameters['active'] == False):
                continue
            del parameters['active']
        # ---
        pipeline_obj = util.load_class("capriqorn.preproc", label)
        if (len(pipeline) > 0):
            parameters['source'] = pipeline[-1]
        print "   " + label
        pipeline.append(pipeline_obj(**parameters))


    # --- pipeline consistency checks
    for i, instance in enumerate(pipeline):
        for label in instance.depends():
            try:
                required_class = util.load_class("capriqorn.preproc_all", label)
            except AttributeError:
                print " Error: Dependency \"" + label + "\" of \"" + \
                    instance.__class__.__name__ + "\" is not available. " + \
                    "Check implementation."
                sys.exit(1)
            for j in xrange(i):
                if isinstance(pipeline[j], required_class):
                    break
            else:
                msg = "pipeline dependency not satisfied: " \
                    + instance.__class__.__name__ + " requires " \
                    + label
                raise RuntimeError(msg)

    for i, instance in enumerate(pipeline):
        for label in instance.conflicts():
            try:
                conflicting_class = util.load_class("capriqorn.preproc_all", label)
            except AttributeError:
                continue
            for j in xrange(i):
                if isinstance(pipeline[j], conflicting_class):
                    msg = "pipeline conflict detected: " \
                        + instance.__class__.__name__ + " conflicts with " \
                        + label
                    raise RuntimeError(msg)


    print " Running pipeline ...",
    sys.stdout.flush()
    pipeline[-1].dump()
    print " done."
    print util.SEP

# # execute code in this .py file only if it is executed as a script, not when it is imported
# if __name__ == "__main__":
#     main()
