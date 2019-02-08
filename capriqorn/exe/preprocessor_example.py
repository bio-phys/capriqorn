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
Generate a preprocessor pipeline parameter file in JSON,
demonstrating the full spectrum of options.

The idea is that the user then edits the JSON file, removes
unnecessary steps and adapts the parameters to his/her needs.
"""
from __future__ import print_function


def main(argparse_args):
    import os
    import sys
    import json

    from cadishi import util
    from .. import testing

    if argparse_args.expert:
        expert_flag = True
    else:
        expert_flag = False

    print(util.SEP)

    template_file = os.path.abspath(os.path.dirname(os.path.abspath(__file__))
                                    + "/../data/preprocessor_template.yaml")
    yaml_file = "preprocessor.yaml"
    data_dir = testing.get_test_data_file_path().rstrip('/')

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

    print(" Preprocessor example input file was written to <" + yaml_file + ">.")
    print(" Adapt it, and run the preprocessor using the command `capriq preproc`.")
    print(util.SEP)
