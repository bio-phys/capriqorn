"""Capriqorn pipeline builder library, used by the pre-/postprocessor executables.
"""
# This file is part of the capriqorn package.  See README.rst,
# LICENSE.txt, and the documentation for details.

from __future__ import print_function
import sys
import numpy as np
import copy
import multiprocessing as mp
from cadishi import base
from cadishi import util
from cadishi import dict_util
from . import parpipe


def create(pipeline_meta, pipeline_module, worker_id=None):
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
        if (worker_id is not None) and \
            ((label == 'ParallelFork') or (label == 'ParallelJoin')):
                parameters['worker_id'] = worker_id
        pipeline_obj = util.load_class(pipeline_module, label)
        if (len(pipeline) > 0):
            parameters['source'] = pipeline[-1]
        print("   " + label)
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


def partial_pipeline_worker(pipeline_segment, pipeline_module, worker_id):
    output_file = "pipeline_" + pipeline_module + '_' + worker_id + '.log'
    util.redirectOutput(output_file)
    # print pipeline_segment
    pipeline = create(pipeline_segment, pipeline_module, worker_id)
    pipeline[-1].dump()
    print(' shutting down ' + worker_id)
    sys.exit(0)


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
    n_workers = 0
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
        segment.append(copy.deepcopy(filter_meta))
        # transfer the number of workers from the ParallelFork to the ParallelJoin filter
        if (label == 'ParallelFork'):
            n_workers = parameters['n_workers']
        if (label == 'ParallelJoin'):
            assert(n_workers > 0)
            parameters['n_workers'] = n_workers
            n_workers = 0
        if (label == 'ParallelFork') or (label == 'ParallelJoin'):
            queue_handles.append(mp.Queue(parpipe.QUEUE_MAXSIZE))
            segment[-1][label]['queue'] = queue_handles[-1]
            segment[-1][label]['side'] = parpipe.SIDE_UPSTREAM
            meta_segments.append(segment)
            segment = []
            segment.append(copy.deepcopy(filter_meta))
            segment[-1][label]['queue'] = queue_handles[-1]
            segment[-1][label]['side'] = parpipe.SIDE_DOWNSTREAM
    meta_segments.append(segment)
    return meta_segments


def run_pipeline(pipeline_meta, pipeline_module):
    (n_parallel, n_workers_per_segment) = get_parallel_configuration(pipeline_meta)

    if (n_parallel <= 0):
        pipeline = create(pipeline_meta, pipeline_module)
        check_dependencies(pipeline, pipeline_module)
        check_conflicts(pipeline, pipeline_module)
        print(" Running sequential pipeline ...", end='')
        sys.stdout.flush()
        pipeline[-1].dump()
    else:
        # counting: reader, writer, parallel workers, workers between parallel regions
        n_workers = sum(n_workers_per_segment)
        print(" Running parallel pipeline with " + str(n_workers) + " worker processes in total...")
        # split pipeline description into per-process parts, obtain queue handles
        meta_segments = get_meta_segments(pipeline_meta)

        # launch child processes to work on the segmented pipeline
        enumerated_segments = [pair for pair in enumerate(meta_segments)]
        last, segment = enumerated_segments[-1]
        mp_pool = []
        for i, segment in enumerated_segments:
            if (i == last):
                # run the last pipeline segment on the present process
                worker_id = 'segment_' + str(i) + '_worker_main'
                pipeline = create(segment, pipeline_module, worker_id)
            else:
                # run any previous pipeline egments on child processes
                for j in range(n_workers_per_segment[i]):
                    worker_id = 'segment_' + str(i) + '_worker_' + str(j)
                    mp_worker = mp.Process(target=partial_pipeline_worker,
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
