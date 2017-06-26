
Theoretical Background
======================

**Macromolecules in solution**

To calculate the **scattering intensities** and **pair-distance distribution functions** of macromolecules in solution from a molecular dynamics trajectory using explicit solvent, we have to account for the finite size and shape of the simulation box to avoid artifacts in the scattering intensity.  To do so, we cut out an **observation volume** containing the macromolecule and a sufficiently thick layer of solvent. 

**Pure solvent simulations**

In experiments, the **difference intensity** between the macromolecule in solution and pure solvent is determined. We therefore also have to simulate pure solvent. In our method, we only need the **particle densities** and **partial radial distribution functions** calculated from these pure solvent simulations. This is in contrast to other methods, where the same observation volume as it is used for the macromolecule in solution, has to be cut out from the solvent trajectory. 

**Self-consistent solvent matching**

Small differences in the solvent densities and structure at the border of the observation volume can lead to artifacts in the small angle regime. To avoid such artifacts, we match solvent properties of the system containing the macromolecule and pure solvent in a layer at the boundary of the observation volume by properly scaling particle densities and partial radial distribution functions.

Method Details
==============

**Pure solvent**

We describe pure solvent by its **particle densities** and **partial radial distribution functions**. These quantities are calculated using **Capriqorn** from a pure solvent simulation in a separate calculation and then provided as input to Capriqorn when analyzing the trajectory of the macromolecule in solution. 

**Macromolecule in solution**

We can choose various **geometries (observation volumes)** to cut the macromolecule and sufficient solvent out of the simulation box. Each of the listed geometries has its own merits. A sphere is the most efficient for globular macromolecules. For all other geometries, we have to use **virtual particles** ("ideal gas" particles) to account for the geometry of the observation volume. 

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
We suggest to use it to get started. You can pick the parameter files for the geometry of your choice and adapt them accordingly.

#. **Prerequisites**

    * Input trajectories
        * PDB file (provides atom names)
        * Trajectory file
    * Mapping of atom names to element names
        Different force fields use different atom names. We have to map these names onto the corresponding element names, which determine the form factors for each element. This information is saved in a file we usually call *alias.dat*. This file contains the atom name provided by the force field in the first column and the element name in the second column. 
        The bash script :download:`get_aliases_initial_guess_from_pdb.sh <./scripts/get_aliases_initial_guess_from_pdb.sh>` extracts atom names from a pdb and provides a first guess of the element names. 
        **!!!YOU HAVE TO EDIT THIS FILE BY HAND AND MAKE CORRECTIONS!!!**  

#. **Pure solvent**
    * We suggest to use orthorombic (cubic) boxes of similar size as the simulation of the macromolecule in solution.  
    * The composition of the pure solvent should be the same as in the simulation of the macromolecule.  


#. **Macromolecule in solution**

    * Preparation of the trajectory
    
        The macromolecule has to be centered in the box, ideally maximizing the solvent thickness around the macromolecule, i.e., maximizing the minimum distance of atoms of the macromolecule to the box borders: 
    
        * Sphere:   Center macromolecule
        * Cuboid:   Center macromolecule and align principal axis with VMD (tcl script :download:`orient.tcl <./scripts/orient.tcl>`) 
        * Ellipsoid: Center macromolecule and align principal axis with VMD (tcl script :download:`orient.tcl <./scripts/orient.tcl>`)
        * Reference: RMSD alignment of the macromolecule with chosen reference structure. 
        * MultiReference: When using the same trajectories as input and reference, nothing has to be done.

        Trajectories can be prepared with VMD (wrapping of the box: http://www.ks.uiuc.edu/Research/vmd/plugins/pbctools/ ) or if you use Gromacs using 
        *trjconv* (*gmx trjconv* in newer versions).
    
    * Preprocessing: capriq preproc -f histograms.yaml 
        * Run the preprocessor for each trajectory separately.
    
    * Histogram calculation: capriq histo -f histograms.yaml 
        * Multiple trajectory h5-files (preprocessor output) can be read in. 
    
    * Postprocessing: capriq postproc -f postprocessor.yaml 
        
        * Multiple histogram h5-files can be read in at once for postprocessing
        * The output is stored in an hdf5 file, which can be unpacked using "capriq unpack" such that the output files are available in ASCII format.  
    
#. **Analysis**
    * Reading in hdf5 files with python (template is coming soon!)


Tips and tricks
===============

* Use VMD to choose geometry. 
    Using selection strings, you can choose representations in VMD which visualize various geometries. 
* The preprocessor can write out xyz files which you can visualize using VMD to check that the macromolecule has been cut out correctly. 

Notes
=====

* Efficiency: 
    * In the current version of the code, the histogram calculation in Cadishi has been highly optimized. Compared to the histogram calculation, the preprocessor, however, can take a significant amount of time as it has not been fully optimized yet. 


