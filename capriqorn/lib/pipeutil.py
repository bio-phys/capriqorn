"""Capriqorn pipeline builder library, used by the pre-/postprocessor executables.
"""
# This file is part of the capriqorn package.  See README.rst,
# LICENSE.txt, and the documentation for details.

import sys
import numpy as np
import copy
import multiprocessing as mp
from cadishi import base
from cadishi import util
from cadishi import dict_util
from . import parpipe


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


def get_parallel_configuration(pipeline_meta):
    """Count the parallel regions of a pipeline specification, moreover,
    the validity of the parallel setup is checked.

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
    n_workers_per_segment = []
    n_workers_per_segment.append(1)
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
                n_workers = parameters['n_workers']
            else:
                n_workers = 1
            n_workers_per_segment.append(n_workers)
        elif (label == 'ParallelJoin'):
            n_join += 1
            n_workers_per_segment.append(1)
        else:
            pass
        if (n_fork - n_join > 1):
            raise RuntimeError("nesting of pipeline parallelism is not allowed")
    if (n_fork != n_join):
        raise RuntimeError("number of ParallelFork and ParallelJoin filters is not equal")
    return (n_fork, n_workers_per_segment)


# def prepare_mp_queues(n_parallel):
#     """Create a list with n_parallel pairs of multiprocessing.JoinableQueue instances."""
#     q_pairs = []
#     for i in range(n_parallel):
#         fork_q = mp.JoinableQueue()
#         join_q = mp.JoinableQueue()
#         q_pairs.append((fork_q, join_q))
#     return q_pairs


def partial_pipeline_worker(pipeline_segment, pipeline_module):
    pipeline = create(pipeline_segment, pipeline_module)


def get_meta_segments(pipeline_meta):
    """Split a pipeline specification into parts following ParallelFork and ParallelJoin
    filters.

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
    meta_segments = []
    queue_handles = []
    segment = []
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
        if (label == 'ParallelFork') or (label == 'ParallelJoin'):
            queue_handles.append(mp.JoinableQueue())
            # add the queue instance to the parameters of the Parallel* filters
            parameters['queue'] = queue_handles[-1]
            parameters['side'] = parpipe.SIDE_UPSTREAM
        segment.append(filter_meta)
        if (label == 'ParallelFork') or (label == 'ParallelJoin'):
            # TODO handle deepcopy correctly
            # meta_segments.append(copy.deepcopy(segment))
            segment = []
            parameters['side'] = parpipe.SIDE_DOWNSTREAM
            segment.append(filter_meta)
    meta_segments.append(segment)
    return meta_segments
