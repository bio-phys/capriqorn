# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.


"""Capriqorn deltaH filter.
"""


import numpy as np
import copy

from cadishi import base
from cadishi import util

from ...lib import rdf
from ...lib import selection
from ...lib import formFactor as ff
from ...lib import pyntensities as pynt


def _make_2d(dict_in):
    """
    Convert a dictionary of 1d NumPy arrays into a
    2d NumPy array.  Return a tuple containing the
    2d array and the sorted list of keys.
    """
    # ---
    assert ('radii' in dict_in.keys())
    # ---
    np_2d = np.zeros((len(dict_in['radii']), len(dict_in.keys())))
    np_2d[:, 0] = (dict_in['radii'])[:]
    np_2d_keys = sorted(dict_in.keys())
    np_2d_keys.remove('radii')
    idx = 1
    for key in np_2d_keys:
        np_2d[:, idx] = (dict_in[key])[:]
        idx += 1
    # ---
    return (copy.deepcopy(np_2d), copy.deepcopy(np_2d_keys))


def _separate_ghosts_from_histogram(H_in):
    """
    Create two disjunct dictionaries from H_in, one (H) containing the real
    species histograms, another (Hx) containing the X particle histograms.
    """
    H = {}
    Hx = {}
    for key in H_in:
        if (key == 'radii'):
            H[key] = H_in[key].copy()
            Hx[key] = H_in[key].copy()
            continue
        if ('X' in key):
            Hx[key] = H_in[key].copy()
        else:
            H[key] = H_in[key].copy()
    return (H, Hx)


# ---
# Implementation mostly follows <lsz/deltaH.py>.
# ---
class DeltaH(base.Filter):
    """A filter that computes the intensity."""
    _depends = ["Solvent"]
    _conflicts = []

    def __init__(self,
                 form_factor_file='atomsf.dat',
                 nq=300,
                 dq=0.01,
                 source=-1,
                 debug=False,
                 verbose=False):
        self.form_factor_file = form_factor_file
        self.nq = nq
        self.dq = dq
        # --- Note: The following two parameters are obtained from the pipeline log!
        self.geometry = None
        self.x_particle_method = None
        # ---
        self.src = source
        self.debug = debug
        self.verb = verbose
        # ---
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def get_meta(self):
        """
        Return information on the present filter,
        ready to be added to a frame object's list of
        pipeline meta information.
        """
        meta = {}
        label = 'DeltaH'
        param = {'form_factor_file': self.form_factor_file,
                 'nq': self.nq,
                 'dq': self.dq,
                 # --- we keep the following two entries for log purposes
                 'geometry': self.geometry,
                 'x_particle_method': self.x_particle_method}
        meta[label] = param
        return meta

    def next(self):
        for hs in self.src.next():
            # hs was chosen to mean 'histogram set' ...
            if hs is not None:
                assert isinstance(hs, base.Container)

                # --- obtain information from the pipeline log
                dr = hs.query_meta('histograms/histogram/dr')
                assert (dr is not None)
                # ---
                self.geometry = hs.get_geometry()
                assert (self.geometry is not None)
                geometry_param = hs.query_meta(self.geometry)
                assert (geometry_param is not None)
                if (self.geometry == 'Sphere' or self.geometry == 'Cuboid' or self.geometry == 'Ellipsoid'):
                    V = geometry_param['volume']
                    assert (V is not None)
                    # VAvg is neede below for MultiReference, where V=1 for histograms
                    # but VAvg is used for densities
                    VAvg = V
                else:
                    # --- for non-sphere geometries, we calculate V using x particles below
                    V = None
                # ---
                virtual_param = hs.query_meta('VirtualParticles')
                if (virtual_param is not None):
                    self.x_particle_method = virtual_param['method']
                    xrho = virtual_param['x_density']
                # ---
                rdf_header = (hs.get_data(base.loc_solv_match + '/g_scaled')).keys()
                rdf_header.remove('radii')
                rdf_elements = util.get_elements(rdf_header)
                n_solv = len(rdf_elements)
                hs_full = selection.get_full(hs)
                n_part_elements = util.get_elements(hs_full.get_data(base.loc_nr_particles).keys())
                histo_elements = util.get_elements(hs_full.get_data(base.loc_histograms).keys())
                # --- print '###', n_part_elements, histo_elements
                assert (n_part_elements == histo_elements)
                n_prot = len(histo_elements)
                if (self.debug):
                    print " rdf_header", rdf_header
                    print " rdf_elements", rdf_elements
                    print " n_solv =", n_solv
                    print " n_prot=", n_prot

                histo = copy.deepcopy(hs_full.get_data(base.loc_histograms))
                nr = len(hs_full.get_data(base.loc_histograms + '/radii'))
                for key in histo.keys():
                    if (key == 'radii'):
                        continue
                    histo[key] *= 2.0

                # --- NOTE : in the following, we're sorting out the virtual particles
                H, Hx = _separate_ghosts_from_histogram(histo)

                # --- consistency checks of the radii
                assert (len(hs.get_data(base.loc_solv_match + '/g_scaled/radii')) >= nr)
                radii_1 = hs.get_data(base.loc_solv_match + '/g_scaled/radii')[0:nr]
                radii_2 = hs_full.get_data(base.loc_histograms + '/radii')[0:nr]
                eps = 1.e-9
                assert np.all(np.fabs(radii_1 - radii_2) < eps)
                #
                rdf_expanded = {}
                for key in (hs.get_data(base.loc_solv_match + '/g_scaled')).keys():
                    # Note: g_scaled dictionary includes the radii array
                    rdf_expanded[key] = np.zeros(nr)
                    (rdf_expanded[key])[0:nr] = (hs.get_data(base.loc_solv_match + '/g_scaled/' + key))[0:nr]
                rdf_org = copy.deepcopy(rdf_expanded)
                # ---
                if (self.debug):
                    hs.put_data(base.loc_delta_h + '/debug/rdf_org', rdf_org)
                rho = hs.get_data(base.loc_solv_match + '/rho')
                # ---
                for key in rdf_expanded.keys():
                    # zero densities as done in the reference code <deltaH.py>
                    if (key == 'radii'):
                        continue
                    (rdf_expanded[key])[0] = 0.0

                if (self.geometry == 'Sphere') and (self.x_particle_method is None):
                    # print "### delta_H :: SPHERE BRANCH ###"
                    R = geometry_param['radius']
                    dHs = copy.deepcopy(H)
                    for key in dHs.keys():
                        if (key == 'radii'):
                            continue
                        (dHs[key])[:] = 0.0
                    dHp = copy.deepcopy(dHs)
                    dH = copy.deepcopy(dHs)
                    # ---
                    assert hs.has_key(base.loc_len_histograms)
                    # --- construct h matrix
                    x_list = hs.get_data(base.loc_len_histograms + '/radii')
                    r_list = H['radii']
                    # --- implement h using a dictionary
                    h_dict = {}
                    for key in hs.get_keys(base.loc_len_histograms):
                        h_dict[key] = np.zeros(len(r_list))
                    h_dict['radii'][:] = r_list[:]
                    # ---
                    pSphere = np.zeros((r_list.shape[0], 2))
                    pSphere[:, 0] = r_list[:]
                    # ---
                    for j, rv in enumerate(r_list):
                        pSphere[j, 1] = rdf.P(rv, R)
                    if (self.debug):
                        hs.put_data(base.loc_delta_h + '/debug/pSphere', pSphere)
                    # ---
                    dx = dr  # DANGER! However, these two should be the same anyway!
                    # ---
                    getSr = rdf.SrFast
                    print
                    for j, rv in enumerate(r_list):
                        if self.verb and (j % 1000 == 0):
                            print " DeltaH:bin ", j
                        Sr = getSr(x_list, R, rv)
                        for key in hs.get_keys(base.loc_len_histograms, skip_keys=['radii']):
                            (h_dict[key])[j] += (hs.get_data(base.loc_len_histograms + '/' + key)[:] * Sr[:]).sum(axis=0)

                    for key in hs.get_keys(base.loc_len_histograms, skip_keys=['radii']):
                        h_dict[key] *= 2.0 * dx / V
                        # --- patch rho[] such that it can be used in the block below
                        if key not in rho:
                            rho[key] = 0.0

                    for key in sorted(H.keys()):
                        if (key == 'radii'):
                            continue
                        # --- patch rdf_expanded such that it can be used below
                        if key not in rdf_expanded:
                            rdf_expanded[key] = np.zeros(nr)
                            # ---
                        (el1, el2) = key.split(',')
                        if (el1 == el2):
                            fac = 1.0
                        else:
                            fac = 2.0
                        # ---
                        (dHs[key])[:] = fac * ((rdf_expanded[key])[:] - 2.0) \
                            * rho[el1] * rho[el2] * V * V * pSphere[:, 1] * dr  # Hx[:,ixx]
                        # ---
                        if (fac == 1):
                            (dHp[key])[:] = (H[key])[:] - V * rho[el1] * (h_dict[el1])[:]  # *Hx[:,ix1]
                        else:
                            (dHp[key])[:] = (H[key])[:] - V * (rho[el2] * (h_dict[el1])[:] +
                                                               rho[el1] * (h_dict[el2])[:])
                        # ---
                        (dH[key])[:] = (dHp[key])[:] - (dHs[key])[:]
                else:
                    # --- virtual particle method branch
                    # print "delta_h "
                    nx = np.mean(hs_full.get_data(base.loc_nr_particles + '/X'), dtype=np.float64)
                    if not (self.geometry == 'Sphere' or self.geometry == 'Cuboid' or self.geometry == 'Ellipsoid'):
                        V = nx / xrho
                    VAvg = V
                    if (self.geometry == 'MultiReferenceStructure'):
                        V = 1.
                        # print " V =", V, "VAvg =", VAvg
                    else:
                        for key in Hx:
                            if key in 'radii':
                                continue
                            pair = key.split(',')
                            assert (len(pair) == 2)
                            if (pair[0] == 'X') and (pair[1] == 'X'):
                                Hx[key] /= (Hx[key]).sum()
                            else:
                                Hx[key] /= nx
                    # ---
                    dHs = copy.deepcopy(H)
                    for key in dHs.keys():
                        if (key == 'radii'):
                            continue
                        (dHs[key])[:] = 0.0
                    dHp = copy.deepcopy(dHs)
                    dH = copy.deepcopy(dHs)
                    # ---
                    for key in sorted(H.keys()):
                        if (key == 'radii'):
                            continue
                        # --- patch rdf_expanded such that it can be used below
                        if key not in rdf_expanded:
                            rdf_expanded[key] = np.zeros(nr)
                        # ---
                        (el1, el2) = key.split(',')
                        # --- patch rho such that it can be used below
                        for el in [el1, el2]:
                            if el not in rho:
                                rho[el] = 0.0
                        # ---
                        if (el1 == el2):
                            fac = 1.0
                        else:
                            fac = 2.0
                        # ---
                        (dHs[key])[:] = fac * ((rdf_expanded[key])[:] - 2.0) \
                            * rho[el1] * rho[el2] * V * V * Hx['X,X']
                        # ---
                        if (fac == 1):
                            (dHp[key])[:] = (H[key])[:] - V * rho[el1] * (Hx[el1 + ',X'])[:]
                        else:
                            (dHp[key])[:] = (H[key])[:] - V * (rho[el2] * (Hx[el1 + ',X'])[:] +
                                                               rho[el1] * (Hx[el2 + ',X'])[:])
                        # ---
                        (dH[key])[:] = (dHp[key])[:] - (dHs[key])[:]
                # ---
                if (self.debug):
                    hs.put_data(base.loc_delta_h + '/debug/rdf_expanded', rdf_expanded)
                    hs.put_data(base.loc_delta_h + '/debug/dHs', dHs)
                    hs.put_data(base.loc_delta_h + '/debug/dHp', dHp)
                    hs.put_data(base.loc_delta_h + '/debug/dH', dH)
                    hs.put_data(base.loc_delta_h + '/debug/H', H)
                    hs.put_data(base.loc_delta_h + '/debug/rho', rho)
                    hs.put_data(base.loc_delta_h + '/debug/h_dict', h_dict)

                # ---
                hs.put_data(base.loc_intensity + '/dH', dH)

                # --- calculate average particle numbers
                nr_part_avg = {}
                for key in hs_full.get_keys(base.loc_nr_particles):
                    nr_part = hs_full.get_data(base.loc_nr_particles + '/' + key)
                    nr_part_avg[key] = nr_part.sum(axis=0) / float(nr_part.shape[0])
                # --- calculate difference
                nr_part_diff = {}
                for key in nr_part_avg:
                    if key in rho:
                        nr_part_diff[key] = nr_part_avg[key] - rho[key] * VAvg
                    else:
                        nr_part_diff[key] = nr_part_avg[key]

                hs.put_data(base.loc_intensity + '/dN', nr_part_diff)

                # --- INTENSITY CALCULATION ---

                # --- read atom form factors from file
                ff_dict = ff.readAtomSFParam(self.form_factor_file)

                # --- prepare 2D input array for library routine
                (dH_2d, dH_2d_keys) = _make_2d(dH)
                if (self.debug):
                    hs.put_data(base.loc_delta_h + '/debug/dH_2d', dH_2d)
                # ---
                _pIntInter, dInter = pynt.intensitiesFFFaster(self.nq, self.dq,
                                                              dH_2d, dH_2d_keys, ff_dict, 1)
                # # --- prepare input
                # nr_part_keys = sorted(nr_part_diff.keys())
                # nr_part_vals = []
                # for key in nr_part_keys:
                #     nr_part_vals.append(nr_part_diff[key])
                # # ---
                # _pIntIntra, dIntra = pynt.intensitiesFFIntraAtom(self.nq, self.dq, \
                #                             nr_part_vals, nr_part_keys, ff_dict)
                # # ---
                # hs.put_data(base.loc_intensity+'/dI_inter', dInter)
                # hs.put_data(base.loc_intensity+'/dI_intra', dIntra)
                dI = dInter.copy()
                # TODO: check, the following line was commented out in <deltaH.py>
                # dI[:,1] += dIntra[:,1]
                hs.put_data(base.loc_intensity + '/dI', dI)

                # --- prepare 2D input array for library routine
                #     (cannot use _make_2d() routine here)
                n_row = len(rdf_org['radii'])
                n_col = len(dH.keys())
                rdf_org_2d = np.zeros((n_row, n_col))
                rdf_org_2d[:, 0] = (rdf_org['radii'])[:]
                rdf_org_2d_keys = sorted(rdf_org.keys())
                rdf_org_2d_keys.remove('radii')
                for key in rdf_org_2d_keys:
                    if key in dH_2d_keys:
                        idx = dH_2d_keys.index(key) + 1
                        rdf_org_2d[:, idx] = (rdf_org[key])[:]
                # ---
                rho_list = []
                rho_keys = sorted(rho.keys())
                for key in ['X', 'X1', 'X2']:
                    if key in rho_keys:
                        rho_keys.remove(key)
                for key in rho_keys:
                    rho_list.append(rho[key])
                # ---
                if (self.debug):
                    hs.put_data(base.loc_delta_h + '/debug/rdf_org_2d', rdf_org_2d)
                # ---
                bulkH = pynt.getBulkIntegrand(rdf_org_2d, rho_list)
                bulkH_keys = dH_2d_keys
                # print "bulkH_keys", bulkH_keys
                _pIntInter, dIntensityInter = pynt.intensitiesFFFaster(self.nq,
                                                                       self.dq, bulkH, bulkH_keys, ff_dict, dr)
                _pIntIntra, dIntensityIntra = pynt.intensitiesFFIntraAtom(self.nq,
                                                                          self.dq, rho_list, rho_keys, ff_dict)
                dIntensity = dIntensityInter.copy()
                dIntensity[:, 1] += dIntensityIntra[:, 1]
                # ---
                hs.put_data(base.loc_intensity + '/I_solv_inter', dIntensityInter)
                hs.put_data(base.loc_intensity + '/I_solv_intra', dIntensityIntra)
                hs.put_data(base.loc_intensity + '/I_solv', dIntensity)

                # TODO: Think about stripping unnecessary information
                # (histograms, length histograms) from hs at this point.

                hs.put_meta(self.get_meta())
                if self.verb:
                    print "DeltaH.next() :", hs.i
                yield hs
            else:
                yield None
