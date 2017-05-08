#!/usr/bin/env python2.7

"""
Generate a postprocessor pipeline parameter file in JSON,
demonstrating the full spectrum of options.

The idea is that the user then edits the JSON file, removes
unnecessary steps and adapts the parameters to his/her needs.

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


def main(argparse_args):
    import sys
    import os
    import json

    from cadishi import util
    from .. import testing

    if argparse_args.expert:
        expert_flag = True
    else:
        expert_flag = False

    print util.SEP

    template_file = os.path.abspath(os.path.dirname(os.path.abspath(__file__))
                                    + "/../data/postprocessor_template.yaml")

    yaml_file = "postprocessor.yaml"
    data_dir = testing.testcase().rstrip('/')

    with open(template_file, 'r') as fp_in, open(yaml_file, 'w') as fp_out:
        template_lines = fp_in.readlines()
        for line in template_lines:
            # apply substitutions
            substring = "__DATA_DIR__"
            if substring in line:
                line = line.replace(substring, data_dir)
            # skip expert parameters if not requested explicitly
            substring = "expert"
            if (not expert_flag) and (substring in line):
                continue
            fp_out.write(line)

    print " Postprocessor example input file was written to <" + yaml_file + ">."
    print " Adapt it, and run run the postprocessor using the command `" + util.get_executable_name() + " postproc`."
    print util.SEP
