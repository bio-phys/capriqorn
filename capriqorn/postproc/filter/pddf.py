# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Capriqorn PDDF filter.

TODO:
* Transition to dictionaries with species combinations as keys instead of
  using monolithic 2D arrays.
"""


import copy
import numpy as np

import cadishi.util as util
from cadishi import base
from ...lib import pddf
from ...lib import formFactor as ff


class PDDF(base.Filter):
    """Computes the PDDF from distance histograms."""
    _depends = ["Solvent", "DeltaH"]
    _conflicts = []

    def __init__(self,
                 # --- parameters were taken from SCalc/example/ePDDF/bulk.par
                 form_factor_file='atomsf.dat',  # atomSFName
                 nbin_coarse=10,  # nBin
                 nq=300,  # nq
                 dq=0.01,  # dq
                 delta=0.01,  # delta
                 dr_intra=0.001,  # drSingle
                 nr_intra=10000,  # nrSingle
                 do_intensity=True,  # previously qFT
                 do_bulk=False,  # compute for bulk solvent (previously qBulk != 0)
                 # ---
                 source=-1,
                 debug=False,
                 verbose=False):
        self.form_factor_file = form_factor_file
        self.nbin_coarse = nbin_coarse
        self.nq = nq
        self.dq = dq
        self.delta = delta
        self.dr_intra = dr_intra
        self.nr_intra = nr_intra
        self.do_intensity = do_intensity
        self.do_bulk = do_bulk
        # --- set-up form factor information
        ffDict = ff.readAtomSFParam(form_factor_file)
        param = ff.reformatSFParam(ffDict)
        self.paramProd = ff.SFParamProd(param)
        # ---
        self.src = source
        self.debug = debug
        self.verb = verbose
        # ---
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """Return information on the present filter, ready to be added to a
        frame object's list of pipeline meta information
        """
        meta = {}
        label = 'PDDF'
        param = {"form_factor_file": self.form_factor_file,
                 "nbin_coarse": self.nbin_coarse,
                 "nq": self.nq,
                 "dq": self.dq,
                 "delta": self.delta,
                 "dr_intra": self.dr_intra,
                 "nr_intra": self.nr_intra,
                 "do_intensity": self.do_intensity,
                 "do_bulk": self.do_bulk}
        meta[label] = param
        return meta

    def next(self):
        for frm in self.src.next():
            if frm is not None:
                # obtain the dr value used to build the histograms
                dr = frm.query_meta('histograms/histogram/dr')
                assert (dr is not None)

                if self.do_bulk:
                    # bulk calculation: we deal with g_scaled instead of dH
                    histograms = frm.get_data(base.loc_solv_match + '/g_scaled')
                    # ... and with the rescaled densities instead of particle numbers
                    dN = frm.get_data(base.loc_solv_match + '/rho')
                else:
                    histograms = frm.get_data(base.loc_intensity + '/dH')  # calculated in delta_H
                    dN = frm.get_data(base.loc_intensity + '/dN')

                dHisto, drPrime = pddf.coarsen_histogram(histograms, self.nbin_coarse, dr)
                if self.debug:
                    frm.put_data(base.loc_pddf + '/histograms_coarse', dHisto)

                # dHistoOrg = copy.deepcopy(dHisto)
                drPrimeOrg = copy.copy(drPrime)
                dr = drPrimeOrg  # reassignment (as done in example code pddf.py)

                if self.do_bulk:
                    n_bins_inv = 1.0 / float(self.nbin_coarse)
                    for key in dHisto:
                        if (key == 'radii'):
                            continue
                        else:
                            dHisto[key][1:] *= n_bins_inv
                            # dHistoOrg[key][1:] *= n_bins_inv
                    dHisto = pddf.bulkSolvHistogram_dict(dHisto, drPrime)
                    # dHistoOrg = pddf.bulkSolvHistogram_dict(dHistoOrg, drPrimeOrg)
                else:
                    pass

                dHistoOrg = copy.deepcopy(dHisto)

                geom = frm.get_geometry()
                R = frm.query_meta('%s/r_max' % geom)
                assert(R is not None)

                nr = int((R + 2) * 2 / dr)
                # ---
                rArray = np.zeros(nr + 1)
                rArray[0] = 0
                for i in range(1, nr + 1):
                    rArray[i] = dr * (i - 0.5)
                rArraySingle = np.zeros(self.nr_intra + 1)
                rArraySingle[0] = 0
                for i in range(1, self.nr_intra + 1):
                    rArraySingle[i] = self.dr_intra * (i - 0.5)
                # ---
                partCF = {}
                partCFArray = np.zeros((len(rArray), len(histograms)))
                partCFArray[:, 0] = rArray

                partCFSingle = {}
                partCFArraySingle = np.zeros((len(rArraySingle), len(histograms)))
                partCFArraySingle[:, 0] = rArraySingle

                CFSum = np.zeros((len(rArray), 2))
                CFSum[:, 0] = rArray[:]

                CFSumSingle = np.zeros((len(rArraySingle), 2))
                CFSumSingle[:, 0] = rArraySingle[:]
                # ---
                # keyList=hs
                # partDHisto={}
                # partDHistoOrg={}
                # for i, key in enumerate(hs):
                #     partDHisto[key]=np.column_stack((dHisto[:,0], dHisto[:,i+1]))
                #     partDHistoOrg[key]=np.column_stack((dHistoOrg[:,0], dHistoOrg[:,i+1]))
                partDHisto = {}
                partDHistoOrg = {}
                keyList = sorted(dHisto.keys())
                keyList.remove('radii')
                for key in keyList:
                    partDHisto[key] = np.column_stack((dHisto['radii'], dHisto[key]))
                    partDHistoOrg[key] = np.column_stack((dHistoOrg['radii'], dHistoOrg[key]))
                    (el1, el2) = key.split(',')
                    if (el1 == el2):
                        if el1 in dN:
                            partDHisto[key][0, 1] = dN[el1]
                        else:
                            partDHisto[key][0, 1] = 0.0
                    else:
                        partDHisto[key][0, 1] = 0.0

                # import sys
                # sys.exit(1)

                # ---
                # for i, key in enumerate(keyList):
                #     print key, paramProd[key]
                #     partCFSingle[key]=getPartCharFunc1(partDHisto, key, paramProd, rArraySingle, drSingle, 0)
                #     partCF[key]=getPartCharFunc2(partDHisto, key, paramProd, rArray, drPrime, delta)
                #     partCF[key]=partCharFuncAdd(partCF[key], partDHistoOrg, key, paramProd, rArray, drPrimeOrg)
                #     partCFArray[:,i+1]=partCF[key][:,1].copy()
                #     partCFArraySingle[:,i+1]=partCFSingle[key][:,1].copy()
                i_mx = len(keyList) - 1
                print("")
                print(util.SEP)
                print(" PPDF: processing histogram %d" % frm.i)
                for i, key in enumerate(keyList):
                    print("   %3d%% (%s)" % (int(100.0 * float(i) / float(i_mx)), key))
                    partCFSingle[key] = pddf.getPartCharFunc1(partDHisto, key,
                                                              self.paramProd, rArraySingle, self.dr_intra, 0)
                    partCF[key] = pddf.getPartCharFunc2(partDHisto, key,
                                                        self.paramProd, rArray, drPrime, self.delta)
                    partCF[key] = pddf.partCharFuncAdd(partCF[key], partDHistoOrg,
                                                       key, self.paramProd, rArray, drPrimeOrg)
                    partCFArray[:, i + 1] = partCF[key][:, 1].copy()
                    partCFArraySingle[:, i + 1] = partCFSingle[key][:, 1].copy()
                print(" PDDF: done")
                print(util.SEP)
                frm.put_data(base.loc_pddf + '/partCF', partCFArray)
                frm.put_data(base.loc_pddf + '/partCFSingle', partCFArraySingle)
                # ---
                # for i in range(len(CFSum)):
                #     CFSum[i,1]=partCFArray[i,1:].sum()
                # np.savetxt(opath+"pddf."+str(int(frameNr))+".dat", CFSum)
                # for i in range(len(CFSumSingle)):
                #     CFSumSingle[i,1]=partCFArraySingle[i,1:].sum()
                # np.savetxt(opath+"pddf.single."+str(int(frameNr))+".dat", CFSumSingle)
                # new, drNew = binning(CFSumSingle, int(drPrime/drSingle), drSingle, distQ=True)
                # CFSum[:len(new),1]+=new[:, 1]
                # np.savetxt(opath+"pddf.tot."+str(int(frameNr))+".dat", CFSum)
                for i in range(len(CFSum)):
                    CFSum[i, 1] = partCFArray[i, 1:].sum()
                frm.put_data(base.loc_pddf + '/CFSum', CFSum)
                for i in range(len(CFSumSingle)):
                    CFSumSingle[i, 1] = partCFArraySingle[i, 1:].sum()
                frm.put_data(base.loc_pddf + '/CFSumSingle', CFSumSingle)
                new, drNew = pddf.binning(CFSumSingle, int(drPrime / self.dr_intra),
                                          self.dr_intra, distQ=True)
                CFSum[:len(new), 1] += new[:, 1]
                frm.put_data(base.loc_pddf + '/pddf_tot', CFSum)
                # ---
                if self.do_intensity:
                    qList = np.arange(0., (self.nq + 1) * self.dq, self.dq)
                    # ---
                    intensity, partInt = pddf.FTCharFunc(partCFArray, dr, qList)
                    frm.put_data(base.loc_pddf + '/intensity_pddf', intensity)
                    frm.put_data(base.loc_pddf + '/partInt_cf', partInt)
                    # ---
                    intensitySingle, partIntSingle = pddf.FTCharFunc(partCFArraySingle,
                                                                     self.dr_intra, qList)
                    frm.put_data(base.loc_pddf + '/intensity_pddf_single', intensitySingle)
                    frm.put_data(base.loc_pddf + '/partInt_cf_single', partIntSingle)
                    # ---
                    intensity_total = intensity.copy()
                    intensity_total[:, 1] += intensitySingle[:, 1]
                    frm.put_data(base.loc_pddf + '/intensity_pddf_total', intensity_total)
                # ---
                frm.put_meta(self.get_meta())
                if self.verb:
                    print "PDDF.next() :", frm.i
                yield frm
            else:
                yield None
