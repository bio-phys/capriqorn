"""Capriqorn pipeline builder library, used by the pre-/postprocessor executables.
"""
# This file is part of the capriqorn package.  See README.rst,
# LICENSE.txt, and the documentation for details.

import sys
import numpy as np
from cadishi import base
from cadishi import util
from cadishi import dict_util


def create(pipeline_meta, pipeline_module):
    """Create pipeline by instantiating Python classes and putting them into a list.

    Parameters
    ----------
    pipeline_meta : list
        List with pipeline element specifications.
    pipeline_module : string
        Python module from which to load the pipeline elements (classes) from.

    Returns
    -------
    list
        List of instantiated classes forming the pipeline.
    """
    pipeline = []
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
        pipeline_obj = util.load_class(pipeline_module, label)
        if (len(pipeline) > 0):
            parameters['source'] = pipeline[-1]
        print "   " + label
        pipeline.append(pipeline_obj(**parameters))
    return pipeline


def check_dependencies(pipeline, pipeline_module):
    """Check pipeline dependencies.

    Parameters
    ----------
    pipeline : list
        List of instantiated classes forming the pipeline.
    pipeline_module : string
        Python module from which to load the pipeline elements (classes) from.

    Raises
    ------
    AttributeError
    RuntimeError
    """
    for i, instance in enumerate(pipeline):
        for label in instance.depends():
            try:
                required_class = util.load_class(pipeline_module, label)
            except AttributeError:
                msg = " Error: Dependency \"" + label + "\" of \"" + \
                    instance.__class__.__name__ + "\" is not available. " + \
                    "Check implementation."
                raise AttributeError(msg)
            for j in xrange(i):
                if isinstance(pipeline[j], required_class):
                    break
            else:
                msg = "pipeline dependency not satisfied: " \
                    + instance.__class__.__name__ + " requires " \
                    + label
                raise RuntimeError(msg)


def check_conflicts(pipeline, pipeline_module):
    """Check pipeline for conflicts.

    Parameters
    ----------
    pipeline : list
        List of instantiated classes forming the pipeline.
    pipeline_module : string
        Python module from which to load the pipeline elements (classes) from.

    Raises
    ------
    RuntimeError
    """
    for i, instance in enumerate(pipeline):
        for label in instance.conflicts():
            try:
                conflicting_class = util.load_class(pipeline_module, label)
            except AttributeError:
                continue
            for j in xrange(i):
                if isinstance(pipeline[j], conflicting_class):
                    msg = "pipeline conflict detected: " \
                        + instance.__class__.__name__ + " conflicts with " \
                        + label
                    raise RuntimeError(msg)


def determine_parallel_configuration(pipeline_meta):
    """Count the parallel regions of a pipeline specification.

    A parallel region is defined by an opening
        ParallelFork filter
    followed by a closing
        ParallelJoin filter.

    Parameters
    ----------
    pipeline_meta : list
        List with pipeline element specifications.

    Raises
    ------
    RuntimeError
    """
    n_fork = 0
    n_join = 0
    n_workers = 0
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
        #print '###', label, parameters
        if (label == 'ParallelFork'):
            n_fork += 1
            if 'n_workers' in parameters:
                n_workers += parameters['n_workers']
            else:
                n_workers += 1
        elif (label == 'ParallelJoin'):
            n_join += 1
        else:
            pass
        if (n_fork - n_join > 1):
            raise RuntimeError("nesting of pipeline parallelism is not allowed")
    if (n_fork != n_join):
        raise RuntimeError("number of ParallelFork and ParallelJoin filters is not equal")
    return (n_fork, n_workers)
