=========
Capriqorn
=========


Introduction
------------

Capriqorn (CAlculation of P(R) and I(Q) Of macRomolecules in solutioN) is a MD
data analysis package written in Python.  It calculates the radial particle-pair
distribution function p(r) and the intensity I(q) from MD frames.

Capriqorn requires the Cadishi package to perform distance histogram
calculations.

Capriqorn was developed, built, and tested on SUSE Linux Enterprise Server 11 SP
4, Ubuntu Linux 14.04 LTS, and Scientific Linux 7 using cPython 2.7.11 from the
Anaconda Python distribution.  It requires NumPy, SciPy, h5py, MDAnalysis and
Cadishi.


Installation
------------

The package is installed in the Pythonic way e.g. as follows::

$ python setup.py install --user  # install into the user's homedirectory

The `install_all_local.sh` file in the repository root may be used to perform
the local installation.  Make sure to add `$HOME/.local/bin` to your PATH
environment variable.


Quick start guide
-----------------

Capriqorn provides a single executable `capriq` that gives access to the
calculations.  Run `capriq --help` to get an overview on the available commands
and options.

To run an example calculation based on the data set included in Capriqorn
proceed as follows::

1. Run `capriq preproc-example` to generate the input file
   `preprocessor.yaml`.  Optionally, adapt the parameter file.
2. Run the preprocessor `capriq preproc`.
3. Run `capriq histo-example` to generate the input file
   `histograms.yaml`.  Optionally, adapt the parameter file.
4. Run `capriq histo`
5. Run `capriq postproc-example` to generate the input file
   `postprocessor.yaml`.  Optionally, adapt the parameter file.
6. Run `capriq postproc`

Note that the steps 3. and 4. are equivalent to the `cadishi` commands.


Licensing
---------

For questions regarding a license or permission to use this software package
for own work, please contact the main author and project leader:

   Juergen Koefinger
   Max Planck Institute of Biophysics
   Theoretical Biophysics
   Max-von-Laue Str. 3
   D-60438 Frankfurt am Main, Germany
   juergen.koefinger@biophys.mpg.de

Unauthorized copying and use is prohibited. All rights reserved.

Copyright 2015 - 2016: Juergen Koefinger, Klaus Reuter, Max Linke
