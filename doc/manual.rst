
Background
==========

**Macromolecules in solution**

To calculate the **scattering intensities** and **pair-distance distribution functions** of macromolecules in solution from a molecular dynamics trajectory using explicit solvent, we have to account for the finite size and shape of the simulation box to avoid artifacts in the scattering intensity.  To do so, we cut out an **observation volume** containing the macromolecule and a sufficiently thick layer of solvent. 

**Pure solvent simulations**

In experiments, the **difference intensity** between the macromolecule in solution and pure solvent is determined. We therefore also have to simulate pure solvent. In our method, we only need the **particle densities** and **partial radial distribution functions** calculated from these pure solvent simulations. This approach is in contrast to other methods, where the same observation volume as it is used for the macromolecule in solution, has to be cut out from the solvent trajectory. 

**Self-consistent solvent matching**

Small differences in the solvent densities and structure at the border of the observation volume can lead to artifacts in the small angle regime. To avoid such artifacts, we match solvent properties of the system containing the macromolecule and pure solvent in a layer at the boundary of the observation volume by properly scaling particle densities and partial radial distribution functions.

Method Details
==============

**Pure solvent**

We describe pure solvent by its **particle densities** and **partial radial distribution functions**. These quantities are calculated using **Capriqorn** from a pure solvent simulation in a separate calculation and then provided as input to Capriqorn when analyzing the trajectory of the macromolecule in solution. 

**Macromolecule in solution**

We we can choose various **geometries (observation volumes)** to cut the macromolecule and sufficient solvent out of the simulation box. 

Choosing the **geometry** we want to 

* increase the signal-to-noise ratio and increase performance by minimizing the amount of bulk solvent while
* including sufficient bulk solvent to avoid finite size effects and to facilitate solvent matching. 

Each of the geometries listed below has its own merits. A sphere is the most efficient geometry for globular macromolecules. For all other geometries, we have to use **virtual particles** ("ideal gas" particles) to account for the geometry of the observation volume which comes with additional computational costs. 

Overview of **observation volume geometries**:

* Sphere
    A sphere centered at the origin is cut out. No virtual particles are needed. 
* Cuboid and Ellipsoid
    Cuboids and ellipsoids are centered at the origin. Their faces/axes are aligned with the coordinate system. The box should be rotated such that the macromolecule is aligned correspondingly (tcl script :download:`orient.tcl <./scripts/orient.tcl>` used with VMD).
* Single reference structure
    A single reference structure is used for all frames to cut out particles within a distance of this reference structure. Minimum number of solvent particles are added, resulting in a better signal to noise ratio. Only a subset of the atoms has to be selected in the reference structure, e.g., select only carbon atoms for a protein. Uses virtual particles. Reference structure should be RMSD aligned with trajectory.
* Multiple reference structures (i.e., a reference trajectory)
    A trajectory is providing reference structures for each frame individually to cut out particles within a distance of the reference structures. Usually, the trajectory used for reference is the same trajectory we want to calculate scattering intensities for. Only a subset of the atoms has to be selected in the reference structure, e.g., select only carbon atoms for a protein. Uses virtual particles. No alignment with coordinate system necessary.


How to use Capriqorn
====================
**Example: Hen egg-white lysozyme**

We provide example input and output files at 
http://ftp.biophys.mpg.de/tbhummer/Capriqorn. 
We suggest to use it to get started. You can pick the parameter files for the geometry of your choice and adapt them accordingly to your problem at hand.

#. **Prerequisites**

    * Input trajectories
        * PDB file (provides atom names)
        * Trajectory file
    * Mapping of atom names to element names
        Different force fields use different atom names. We have to map these names onto the corresponding element names, which determine the form factors for each element. This information is saved in a file we usually call *alias.dat*. This file contains the atom name provided by the force field in the first column and the element name in the second column. 
        The bash script :download:`get_aliases_initial_guess_from_pdb.sh <./scripts/get_aliases_initial_guess_from_pdb.sh>` extracts atom names from a pdb and provides a first guess of the element names. 
        **!!!YOU HAVE TO EDIT THIS FILE BY HAND AND MAKE CORRECTIONS!!!**  

#. **Pure solvent**
    * We suggest to use orthorhombic (cubic) boxes of similar size (or larger) as the simulation box used for the macromolecule in solution.  
    * The force field and composition of the pure solvent should be the same as in the simulation of the macromolecule.  

#. **Macromolecule in solution**

    * Preparation of the trajectory
    
        The macromolecule has to be centered in the box, ideally maximizing the solvent thickness around the macromolecule, i.e., maximizing the minimum distance of atoms of the macromolecule to the box borders: 
    
        * Sphere:   Center macromolecule at origin.
        * Cuboid:   Center macromolecule at origin and align principal axis with VMD (tcl script :download:`orient.tcl <./scripts/orient.tcl>`) 
        * Ellipsoid: Center macromolecule at origin and align principal axis with VMD (tcl script :download:`orient.tcl <./scripts/orient.tcl>`)
        * Reference: RMSD alignment of the macromolecule with chosen reference structure. 
        * MultiReference: When using the same trajectories as input and reference, no alignment is necessary.

        Trajectories can be prepared with VMD (wrapping of the box: http://www.ks.uiuc.edu/Research/vmd/plugins/pbctools/ ) or if you use Gromacs using 
        *trjconv* (*gmx trjconv* in newer versions Gromacs).
    
    * Preprocessing: capriq preproc -f preprocessor.yaml 
        * Run the preprocessor for each trajectory separately. The preprocessor can be run in parallel over a single node.  Also note that splitting the trajectory in multiple files facilitates further trivial parallelization of the preprocessor. 
    
    * Histogram calculation: capriq histo -f histograms.yaml 
        * Multiple trajectory h5-files (preprocessor output) can be read in. We use Cadishi to efficiently calculate histograms on CPUs and/or GPUs.
    
    * Postprocessing: capriq postproc -f postprocessor.yaml 
        * Multiple histogram h5-files can be read in at once for postprocessing.
        * The output is stored in an hdf5 file, which can be unpacked using "capriq unpack" such that the output files are available in ASCII format.  
    
#. **Analysis**
    * Reading in hdf5 files with python (template is coming soon!)


Tips and tricks
===============

* Use VMD to choose geometry. 
    Using selection strings, you can choose representation in VMD which visualize various geometries. 
    Note that the selection string syntax in VMD is different to the one used in Capriqorn (Capriqorn using MD Analysis which uses CHARMM syntax).
* The preprocessor can write out xyz files which you can visualize using VMD to check that the macromolecule has been cut out correctly. 
* Capriqorn offers a plethora of methods and modules. 
  See the example parameter files for an overview. 
  The files can be written via the command capriq example [--expert]
  The `--expert` switch adds additional options which allow to override some default values.  Some hints on the parameter choices, the general usage, and the file handling are given in the following.  

    * For various reasons Capriqorn uses HDF5 files. To inspect a HDF5 file, use
      a viewer software or extract the HDF5 file using the Capriqorn command
      ``capriq unpack``.
    * Compression of the HDF5 output datasets using the LZF algorithm is usually
      beneficial regarding performance and file size. LZF comes with h5py by default.
      Other installations and tools may lack LZF, so use no compression or
      gzip compression in case you need to interact with such software.  You can use
      the ``capriq merge`` tool to change the compression of a file.

* An essential part of the Capriqorn pipeline consists of the distance histogram
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


Notes
=====

* Efficiency: 
    * In the current version of the code, the histogram calculation in Cadishi has been highly optimized. Compared to the histogram calculation, the preprocessor, however, can take a significant amount of time as it has not been fully optimized yet.
    * The preprocessor pipeline can be parallelized using the ParallelFork() and ParallelJoin() filters.

