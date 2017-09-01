=========
Capriqorn
=========


Introduction
------------

Capriqorn (CAlculation of P(R) and I(Q) Of macRomolecules in solutioN) is a molecular dynamics (MD)
data analysis package written in Python.  It calculates the radial particle-pair
distribution function p(r) and the intensity I(q) from MD frames.

Capriqorn requires the Cadishi package to perform distance histogram
calculations.

Capriqorn was developed, built, and tested on SUSE Linux Enterprise Server 11 SP
4, Ubuntu Linux 14.04 LTS, and Scientific Linux 7 using cPython 2.7.11 from the
Anaconda Python distribution.  It requires NumPy, SciPy, h5py, MDAnalysis and
Cadishi.

Documentation
-------------

Please visit `local site <doc/html/index.html>`_.


Installation
------------

The package is installed in the Pythonic way e.g. as follows::

$ python setup.py install --user  # install into the user's home directory

Make sure to add `$HOME/.local/bin` to your PATH environment variable.


Quick start guide
-----------------

Capriqorn provides a single executable `capriq` that gives access to the
calculations.  Run `capriq --help` to get an overview on the available commands
and options.

To run an example calculation based on the data set included in Capriqorn
proceed as follows::

1. Run `capriq preproc` to generate the necessary YAML input files for the preprocessor, the histogram calculation, and the postprocessor. Optionally, inspect and adapt the parameter files.
2. Run the preprocessor `capriq preproc`.
4. Run `capriq histo`
6. Run `capriq postproc`

Note that the step 2 is equivalent to the `cadishi` commands.


Licensing
---------

Capriqorn is released under the GPLv2 license. See the file 
`LICENSE.txt` for details.

Copyright 2015 - 2017: Juergen Koefinger, Klaus Reuter, Max Linke


CITATION
--------

Please cite 

| `Atomic-resolution structural information from scattering experiments on macromolecules in solution <https://journals.aps.org/pre/pdf/10.1103/PhysRevE.87.052712>`_
| Jürgen Köfinger and Gerhard Hummer
| Phys. Rev. E 87, 052712 (2013)

For your convenience, we provide citations in :download:`bibtex <./citations/PhysRevE.87.052712.bibtex>` format and :download:`endnote  <./citations/PhysRevE.87.052712.ris>` format.
