Tips and tricks
===============

Capriqorn
---------

Capriqorn offers a plethora of methods and modules. See the example parameter
files for an overview. The files can be written via the command::

   capriq example [--expert]

The `--expert` switch adds additional options which allow to override some default
values.

Some hints on the parameter choices, the general usage, and the file handling
are given in the following.

* For various reasons Capriqorn uses HDF5 files. To inspect a HDF5 file, use
  a viewer software or extract the HDF5 file using the Capriqorn command
  ``capriq unpack``.

* Compression of the HDF5 output datasets using the LZF algorithm is usually
  beneficial regarding performance and file size. LZF comes with h5py by default.
  Other installations and tools may lack LZF, so use no compression or
  gzip compression in case you need to interact with such software.  You can use
  the ``capriq merge`` tool to change the compression of a file.


Cadishi --- Distance histogram calculation
------------------------------------------

An essential part of the Capriqorn pipeline consists of the distance histogram
calculation performed by the Cadishi package.  Cadishi offers many parameters
which allow to tune and optimize the performance.  As a quick start one may try
the following configuration via the parameter file:

* adapt the number of CPU workers to the number of CPU sockets you have in your
  system;
* adapt the number of threads per CPU worker to the number of cores you have per
  socket, however, consider the following point:
* when choosing the thread numbers reserve one core each for the input and output
  processes and for the GPU processes (if applicable);
* pinning the processes to NUMA domains is usually a good idea;
* example: On a dual socket system with 8 cores per socket and two GPUs one may
  start with the following configuration: 2 CPU workers, 6 threads per CPU worker,
  2 GPU workers.

By default Cadishi uses a reasonable process and thread configuration.
