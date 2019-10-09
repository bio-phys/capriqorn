# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

"""Capriqorn (parallel) pipeline builder library, used by the pre-/postprocessor executables.
"""

from __future__ import print_function
from builtins import str
from builtins import range
import os
import sys
import time
import signal
import copy
import multiprocessing as mp
import numpy as np
from cadishi import base
from cadishi import util
from cadishi import dict_util
from . import parpipe


def instantiate_pipeline(pipeline_meta, pipeline_module, worker_id=None):
    """Create pipeline by instantiating Python classes and putting them into a list.

    Parameters
    ----------
    pipeline_meta : list
        List with pipeline element specifications.
    pipeline_module : string
        Python module from which to load the pipeline elements (classes) from.
    worker_id : string
        Optional string identifying a parallel worker.  For debug/log purposes.

    Returns
    -------
    list
        List of instantiated classes forming the pipeline.
    """
    pipeline = []
    print(util.SEP)
    msg = " Pipeline configuration"
    if worker_id is not None:
        msg += " for worker `" + worker_id + "'"
    msg += ":"
    print(msg)
    for filter_meta in pipeline_meta:
        assert (len(filter_meta) == 1)
        label = ""
        parameters = {}
        for (label, parameters) in filter_meta.items():
            # we leave the loop immediately since filter_meta must have only a single item
            break
        if 'active' in parameters:
            if (parameters['active'] == False):
                continue
            del parameters['active']
        if (worker_id is not None) and ((label == 'ParallelFork') or (label == 'ParallelJoin')):
            parameters['worker_id'] = worker_id
        pipeline_obj = util.load_class(pipeline_module, label)
        if (len(pipeline) > 0):
            parameters['source'] = pipeline[-1]
        print("   " + label)
        pipeline.append(pipeline_obj(**parameters))
    print(util.SEP)
    return pipeline


def check_filter_dependencies(pipeline, pipeline_module):
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
            for j in range(i):
                if isinstance(pipeline[j], required_class):
                    break
            else:
                msg = "pipeline dependency not satisfied: " \
                    + instance.__class__.__name__ + " requires " \
                    + label
                raise RuntimeError(msg)


def check_filter_conflicts(pipeline, pipeline_module):
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
            for j in range(i):
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

    Returns
    -------
    Tuple with (the number of parallel forks, the number of workers per segment).
    """
    n_fork = 0
    n_join = 0
    n_workers = 0
    n_workers_per_segment = []
    n_workers_per_segment.append(1)
    for filter_meta in pipeline_meta:
        assert (len(filter_meta) == 1)
        label = ""
        parameters = {}
        for (label, parameters) in filter_meta.items():
            # we leave the loop immediately since filter_meta must have only a single item
            break
        if (label == 'ParallelJoin') and (n_workers == 0):
            continue
        if 'active' in parameters:
            if (parameters['active'] == False):
                continue
            del parameters['active']
        if (label == 'ParallelFork'):
            n_fork += 1
            n_workers = parameters['n_workers']
            # sanitize an invalid number of workers
            if (n_workers <= 0):
                n_workers = 1
                parameters['n_workers'] = n_workers
            n_workers_per_segment.append(n_workers)
        elif (label == 'ParallelJoin'):
            n_join += 1
            n_workers_per_segment.append(1)
            n_workers = 0  # reset n_workers flag
        else:
            pass
        if (n_fork - n_join > 1):
            raise RuntimeError("nesting of pipeline parallelism is not allowed")
    if (n_fork != n_join):
        raise RuntimeError("number of ParallelFork and ParallelJoin filters is not equal")
    return (n_fork, n_workers_per_segment)


def pipeline_segment_worker(pipeline_segment, pipeline_module, worker_id):
    """Function launched in multiprocessing child processes ("workers") in order
    to run a pipeline segment.

    Parameters
    ----------
    pipeline_segment : list
        List with instantiated pipeline classes.
    pipeline_module : string
        Python module from which to load the pipeline elements (classes) from.
    worker_id : string
        Optional string identifying a parallel worker.  For debug/log purposes.

    Returns
    -------
    Nothing, quits process with exit status "0" on success.
    """
    output_file = "./pipeline_log/" + pipeline_module + '_' + worker_id + '.log'
    util.md(output_file)
    util.redirectOutput(output_file)
    pipeline = instantiate_pipeline(pipeline_segment, pipeline_module, worker_id)
    check_filter_dependencies(pipeline, pipeline_module)
    check_filter_conflicts(pipeline, pipeline_module)
    try:
        pipeline[-1].dump()
    except:
        print(" Exception detected in `" + worker_id + "'.")
        print(" Sending shutdown signal to master process. Goodbye.")
        print(util.SEP)
        os.kill(os.getppid(), signal.SIGUSR1)
        raise
        sys.exit(1)
    else:
        print(" Shutting down `" + worker_id + "'.")
        print(util.SEP)
        sys.exit(0)


def get_pipeline_meta_segments(pipeline_meta):
    """Split a pipeline specification into parts according to ParallelFork and ParallelJoin
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

    Returns
    -------
    list
        List of pipeline specifications, with information on parallelism and the
        multiprocessing queues (to handle IPC) added to the Parallel* filters
    """
    n_workers = 0
    meta_segments = []
    queue_handles = []
    segment = []
    for filter_meta in pipeline_meta:
        assert (len(filter_meta) == 1)
        label = ""
        parameters = {}
        for (label, parameters) in filter_meta.items():
            # we leave the loop immediately since filter_meta must have only a single item
            break
        # disable ParallelJoin in case ParallelFork is not enabled
        if (label == 'ParallelJoin') and (n_workers == 0):
            continue
        if 'active' in parameters:
            if (parameters['active'] == False):
                continue
            del parameters['active']
        # transfer the number of workers from the ParallelFork to the ParallelJoin filter
        if (label == 'ParallelFork'):
            n_workers = parameters['n_workers']
            if (n_workers <= 0):
                # we use the zero value as a flag to indicate a disabled configuration
                n_workers = 0
                continue
        segment.append(copy.deepcopy(filter_meta))
        if (label == 'ParallelJoin'):
            # the downstream side of join needs to know the number of workers
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


# List containing the multiprocessing workers.
mp_pool = []
# flag to avoid the signal handler act multiple times
mp_shutdown_recv = False
# We define a signal handler here to be able to catch errors from child
# processes, the parameters of signal handlers don't allow to pass values,
# but we need 'mp_pool' from outside.
def pipeline_master_unexpectedShutdownHandler(signum, frame):
    """Singnal handler to catch SIGUSR1 and SIGTERM sent by child processes."""
    global mp_shutdown_recv
    print(" Master: Shutdown signal received from child process!")
    if not mp_shutdown_recv:
        mp_shutdown_recv = True
        # give bogus child time to re-raise the exception
        time.sleep(1.0)
        print(" Master: Emergency shotdown, killing all child processes.")
        print(" Master: See the files in './pipeline_log/' to learn about the cause.")
        for mp_worker in mp_pool:
            mp_worker.terminate()
        print(" Master: Killing master process. Goodbye.")
        print(util.SEP)
        os.kill(os.getpid(), signal.SIGTERM)
        os.kill(os.getpid(), signal.SIGKILL)

def run_pipeline(pipeline_meta, pipeline_module):
    """Run pipeline by dividing the pipeline into segments, setting up the
    actual pipeline segments and running them on multiprocessing workers.

    Parameters
    ----------
    pipeline_meta : list
        List with pipeline element specifications.
    pipeline_module : string
        Python module from which to load the pipeline elements (classes) from.

    Returns
    -------
    Nothing on success.
    """
    (n_parallel, n_workers_per_segment) = get_parallel_configuration(pipeline_meta)
    # print(" DBG: parallel configuration:" + str((n_parallel, n_workers_per_segment)))
    if (n_parallel <= 0):
        # sanitize the pipeline meta information
        meta_segments = get_pipeline_meta_segments(pipeline_meta)
        pipeline = instantiate_pipeline(meta_segments[0], pipeline_module)
        # print(" DBG: pipeline:" + str(pipeline))
        check_filter_dependencies(pipeline, pipeline_module)
        check_filter_conflicts(pipeline, pipeline_module)
        print(" Running sequential pipeline ...", end='')
        sys.stdout.flush()
        pipeline[-1].dump()
    else:
        # counting: reader, writer, parallel workers, workers between parallel regions
        n_workers = sum(n_workers_per_segment)
        print(" Running parallel pipeline with " + str(n_workers) + " worker processes in total ...")
        # split pipeline description into per-process parts, obtain queue handles
        meta_segments = get_pipeline_meta_segments(pipeline_meta)
        # print(" DBG: meta_segments:" + str(meta_segments))
        # launch child processes to work on the segmented pipeline
        enumerated_segments = [pair for pair in enumerate(meta_segments)]
        last, segment = enumerated_segments[-1]
        for i, segment in enumerated_segments:
            if (i == last):
                # run the last pipeline segment on the present process
                worker_id = 'segment_' + str(i) + '_worker_main'
                pipeline = instantiate_pipeline(segment, pipeline_module, worker_id)
            else:
                # run any previous pipeline egments on child processes
                for j in range(n_workers_per_segment[i]):
                    worker_id = 'segment_' + str(i) + '_worker_' + str(j)
                    mp_worker = mp.Process(target=pipeline_segment_worker,
                                           args=(segment, pipeline_module, worker_id))
                    mp_pool.append(mp_worker)
        for mp_worker in mp_pool:
            mp_worker.start()
        sys.stdout.flush()
        # install the shutdown handler for SIGUSR1 events received from child processes
        signal.signal(signal.SIGUSR1, pipeline_master_unexpectedShutdownHandler)
        # launch the last segment of the pipeline
        try:
            pipeline[-1].dump()
        except:
            print(" Master: Exception detected in master process.")
            print(" Master: Sending shutdown signal to all processes. Goodbye.")
            for mp_worker in mp_pool:
                mp_worker.terminate()
            print(util.SEP)
            raise
        else:
            # all the child processes should be finished until now, nevertheless we join() them
            for mp_worker in mp_pool:
                mp_worker.join()
