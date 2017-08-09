"""Capriqorn ParallelFork() and ParallelJoin() parallelization filters.

The parallel filters are used to exploit data parallelism in pipelines. It uses
the Python multiprocessing module, see <pipeutil.py> for the implementation.

Say, we would like to parallelize a pipeline consisting of

         r f f f f w

i.e. a reader, four filters, and a writer.  Assume that the innermost two filters
may trivially run in parallel.  Using the parallel filter we are able to achieve
this as follows e.g. using five processes:

         r        reader                process 0
         f        filter
         o        parallel fork
------------------------------------------------------------
    o    o    o   parallel fork         process 1,2,3
    f    f    f
    f    f    f
    o    o    o   parallel join
------------------------------------------------------------
         o        parallel join         process 4
         f        filter
         w        writer

Status: OK, including order preservation, see also <pipeutil.py>.
"""

# from __future__ import print_function

__author__ = "Klaus Reuter"
__copyright__ = "Copyright (C) 2015-2017 Juergen Koefinger, Klaus Reuter"
__license__ = "license_tba"

from cadishi import base


# integer constants to be used to specify the side we're on
SIDE_UNDEFINED=0
SIDE_UPSTREAM=1
SIDE_DOWNSTREAM=2
# max. elements before the queue.put() function blocks, see <pipeutil.py>
QUEUE_MAXSIZE=32


class ParallelFork(base.Filter):
    """Filter to indicate the start of a parallel region of a pipeline."""
    _depends = []
    _conflicts = []

    def __init__(self, source=-1, verbose=False,
                 queue=None, side=SIDE_UNDEFINED, n_workers=0, worker_id=''):
        """
        Parameters
        ----------
        source : filter class instance with generator
        verbose : boolean
        queue : multiprocessing queue
        side : int
            Integer indicating the side: SIDE_UNDEFINED, SIDE_UPSTREAM, SIDE_DOWNSTREAM
        n_workers : int
            Number of workers used for the parallel region.
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
                 'n_workers': self.n_workers,
                 'worker_id': self.worker_id}
        meta[label] = param
        return meta

    def next(self):
        """Generator-style method which pulls objects from the queue and
        yields them. To be used downstream-wise."""
        if self.verb:
            print(self.__class__.__name__ + '.next() : ' + self.worker_id)
        while True:
            obj = self.queue.get()
            if isinstance(obj, base.Container):
                obj.put_meta(self.get_meta())
            yield obj
            if obj is None:
                break

    def dump(self):
        """Generator-style method which gets objects by calling the previous
        class'es next() function and puts the objects into the queue. To be used
        upstream-wise.

        The method counts the container objects and adds a number to each of them.
        The ParallelJoin filter evaluates these to preserve the ordering.
        """
        counter = 0
        if self.verb:
            print(self.__class__.__name__ + '.dump() : ' + self.worker_id)
        for obj in self.src.next():
            # on the upstream side of ParallelFork, we count and mark each container object
            if isinstance(obj, base.Container):
                obj.put_data(base.loc_parallel + '/number', counter)
                counter += 1
                obj.put_meta(self.get_meta())
            self.queue.put(obj)
        # finally, put as many Nones into the queue as there are workers to indicate to quit
        for i in range(self.n_workers):
            self.queue.put(None)


class ParallelJoin(base.Filter):
    """Filter to indicate the stop of a parallel region of a pipeline."""
    _depends = []
    _conflicts = []

    def __init__(self, source=-1, verbose=False,
                 queue=None, side=SIDE_UNDEFINED, n_workers=0, worker_id=''):
        """
        Parameters
        ----------
        source : filter class instance
        verbose : boolean
        queue : multiprocessing queue
        side : int
            Integer indicating the side: SIDE_UNDEFINED, SIDE_UPSTREAM, SIDE_DOWNSTREAM
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
        label = 'ParallelJoin'
        param = {'side': self.side,
                 'n_workers': self.n_workers,
                 'worker_id': self.worker_id}
        meta[label] = param
        return meta

    def next(self):
        """Generator-style method which pulls objects from the queue and
        yields them. To be used downstream-wise.

        Preserves the initial ordering of the container objects thanks to the
        numbering added by the ParallelFork filter.
        """
        if self.verb:
            print(self.__class__.__name__ + '.next() : ' + self.worker_id)
        buf = {}
        finished = False
        none_counter = 0
        yield_counter = 0
        valid_counter = 0
        while True:
            if not finished:
                try:
                    obj = self.queue.get(False, 0.5)
                    if isinstance(obj, base.Container):
                        number = obj.get_data(base.loc_parallel + '/number')
                        obj.del_data(base.loc_parallel)
                        obj.put_meta(self.get_meta())
                        buf[number] = obj
                        valid_counter += 1
                        if self.verb:
                            print("  buffr'd: " + str(number))
                    else:
                        none_counter += 1
                except Exception, e:
                    pass
            else:
                break
            # yield all pending objects
            while True:
                if yield_counter in buf:
                    yield buf[yield_counter]
                    del buf[yield_counter]
                    if self.verb:
                        print("  yield'd: " + str(yield_counter))
                    yield_counter += 1
                else:
                    break
            if (none_counter == self.n_workers):
                finished = True
        # The following remainder branch should never be entered:
        if (len(buf) > 0):
            for key in sorted(buf.iterkeys()):
                yield buf[key]
                if self.verb:
                    print("  yield'r: " + str(key))
        yield None

    def dump(self):
        """Generator-style method which gets objects by calling the previous
        class'es next() function and puts the objects into the queue. To be used
        upstream-wise."""
        if self.verb:
            print(self.__class__.__name__ + '.dump() : ' + self.worker_id)
        for obj in self.src.next():
            if isinstance(obj, base.Container):
                obj.put_meta(self.get_meta())
            self.queue.put(obj)
        # for i in range(self.n_workers):
        #     self.queue.put(None)
