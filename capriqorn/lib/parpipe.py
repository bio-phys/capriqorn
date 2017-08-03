"""Capriqorn parallelization filter

The parallel filter is used to exploit data parallelism in pipelines.  It uses
the Python multiprocessing module, see <pipeutil.py>.

Say we would like to parallelize a pipeline consisting of

         r f f f f w

i.e. a reader, four filters, and a writer.  Assume that the innermost two filters
may trivially run in parallel.  Using the parallel filter we are able to achieve
this as follows e.g. using five processes:

         r        reader                process 0
         f        filter
         o        parallel fork
------------------------------------------------------------
    o    o    o   parallel fork         process 2, 3, 4
    f    f    f
    f    f    f
    o    o    o   parallel join
------------------------------------------------------------
         o        parallel join         process 1
         f        filter
         w        writer


The pipeline setup needs to be implemented as follows:

* pipeline must be set up piecewise per process
* parallel zones are defined between fork and join
* central question is when the fork shall take place
* multiprocessing queues must be created before the fork

Algorithm:
* parse and check pipeline setup once
* count parallel regions, determine the number of processes needed
* prepare multiprocessing queues, arrange them in a list and pass the
  correct one to the respective worker
* launch the worker, close any queues which are not needed
"""

from __future__ import print_function

__author__ = "Juergen Koefinger, Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2017 Juergen Koefinger, Klaus Reuter"
__license__ = "license_tba"

from cadishi import base


# integer constants to be used to specify the side we're on
SIDE_BOTH=0
SIDE_UPSTREAM=1
SIDE_DOWNSTREAM=2
# max. elements before the queue.put() function blocks, see <pipeutil.py>
QUEUE_MAXSIZE=32


class ParallelFilter(base.Filter):
    """Common base class for the ParallelFork and ParallelJoin classes."""

    def next(self):
        """Generator-style method which pulls objects from the queue and
        yields them. To be used downstream-wise."""
        if self.verb:
            print(self.__class__.__name__ + ', next(), ' + self.worker_id)
        while True:
            obj = self.queue.get()
            yield obj
            # NOTE: The following 'break' condition is the terminal trigger for the parallel pipeline!
            if obj is None:
                break

    def dump(self):
        """Generator-style method which gets objects by calling the previous
        class'es next() function and puts the objects into the queue. To be used
        upstream-wise."""
        if self.verb:
            print(self.__class__.__name__ + ', dump(), ' + self.worker_id)
        for obj in self.src.next():
            self.queue.put(obj)
        for i in range(self.n_workers):
            self.queue.put(None)


class ParallelFork(ParallelFilter):
    """Filter to indicate the start of a parallel region of a pipeline."""
    _depends = []
    _conflicts = []

    def __init__(self, source=-1, verbose=False, queue=None, side=SIDE_BOTH,
                 n_workers=0, worker_id=''):
        """
        Parameters
        ----------
        source : filter class instance
        verbose : boolean
        queue : multiprocessing queue
        side : int
            Integer indicating the side: SIDE_BOTH, SIDE_UPSTREAM, SIDE_DOWNSTREAM
        n_workers : int
        worker_id : string
            String to identify the present worker.
        """
        self.src = source
        self.verb = verbose
        self.queue = queue
        self.side = side
        self.n_workers = n_workers
        self.worker_id = worker_id

    def get_meta(self):
        """ Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information.
        """
        meta = {}
        label = 'ParallelFork'
        param = {'side': self.side,
                 'n_workers': self.n_workers}
        meta[label] = param
        return meta


class ParallelJoin(ParallelFilter):
    """Filter to indicate the stop of a parallel region of a pipeline."""
    _depends = []
    _conflicts = []

    def __init__(self, source=-1, verbose=False, queue=None, side=SIDE_BOTH,
                 n_workers=0, worker_id=''):
        """
        Parameters
        ----------
        source : filter class instance
        verbose : boolean
        queue : multiprocessing queue
        side : int
            Integer indicating the side: SIDE_BOTH, SIDE_UPSTREAM, SIDE_DOWNSTREAM
        n_workers : int
        worker_id : string
            String to identify the present worker.
        """
        self.src = source
        self.verb = verbose
        self.queue = queue
        self.side = side
        self.n_workers = n_workers
        self.worker_id = worker_id

    def get_meta(self):
        """ Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information.
        """
        meta = {}
        label = 'ParallelFork'
        param = {'side': self.side}
        meta[label] = param
        return meta



# --- code below is obsolete ---


# class Parallel(base.Filter):
#     """A filter that puts base.Container() objects into a queue and fetches
#     the results from another queue, in order to allow to parallelize the
#     pipeline of generators.
#     """
#     _depends = []
#     _conflicts = []
#
#     def __init__(self, source=-1, verbose=False, input_queue=None,
#                  output_queue=None, worker_id=-1, n_workers=1):
#         """ Initialize instance of parallel class.
#         worker_id is zero or positive only in parallel setups.
#         """
#         self.src = source
#         self.verb = verbose
#         if (worker_id >= 0):
#             if (input_queue is None):
#                 assert(output_queue is not None)
#             if (output_queue is None):
#                 assert(input_queue is not None)
#         self.input_queue = input_queue
#         self.output_queue = output_queue
#         self.worker_id = worker_id
#         self.n_workers = n_workers  # total number of processes
#         self._depends.extend(super(base.Filter, self)._depends)
#         self._conflicts.extend(super(base.Filter, self)._conflicts)
#
#     def get_meta(self):
#         """ Return information on the present filter, ready to be added to a
#         frame object's list of pipeline meta information.
#         """
#         meta = {}
#         label = 'Parallel'
#         param = {'worker_id': worker_id,
#                  'n_workers': n_workers}
#         meta[label] = param
#         return meta
#
#     def next(self):
#         if (self.worker_id < 0):
#             # do not use multiprocessing, act as a dummy generator
#             for frame in self.src.next():
#                 assert isinstance(frame, base.Container)
#                 frame.put_meta(self.get_meta())
#                 if self.verb:
#                     print "Parallel.next() :", frame.i
#                 yield frame
#         elif (self.worker_id == 0):
#             # use multiprocessing, read from a generator, put objects into queue
#             for frame in self.src.next():
#                 assert isinstance(frame, base.Container)
#                 frame.put_meta(self.get_meta())
#                 if self.verb:
#                     print "Parallel.next() :", frame.i
#                 self.input_queue.put(frame)
#             for i in range(self.n_workers-2):
#                 # send None in order to communicate that the work is done
#                 frame = None
#                 self.input_queue.put(frame)
#         elif (self.worker_id == 1):
#             # while we read successfully from the output queue ...
#             while True:
#                 frame = self.output_queue.get(frame)
#                 # catch None as a signal that no more work is to be done
#                 if frame is None:
#                     break
#                 yield frame
#         else:
#             # task working on the central part of the pipeline:
#             # we differentiate between the opening and the closing filter
#             # simply by evaluating the presence of the queues
#             if (self.input_queue is not None):
#                 while True:
#                     frame = self.input_queue.get(frame)
#                     if frame is None:
#                         break
#                     yield frame
#             elif (self.output_queue is not None):
#                 for frame in self.src.next():
#                     assert isinstance(frame, base.Container)
#                     frame.put_meta(self.get_meta())
#                     self.output_queue.put(frame)
#             else:
#                 pass
