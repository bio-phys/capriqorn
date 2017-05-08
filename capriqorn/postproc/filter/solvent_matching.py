"""Capriqorn filter library <postproc_filter_solvent_matching.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""


import numpy as np
import scipy.interpolate as sint
from six.moves import range

from cadishi import base
from cadishi.io import hdf5

from ...lib import selection
from ...lib import rdf


class Solvent(base.Filter):
    """A filter that performs self-consistent solvent matching."""
    _depends = []
    _conflicts = []

    def __init__(self, source=-1,
                 g_ascii_file="rdf.extended.dat",
                 g_match='O,O',
                 g_scaled_file=None,  # optional: HDF5 file to read g_scaled from
                 g_plateau_fraction=0.3,  # fraction of the distance range of the rdfs, where the rdfs are flat
                 g_noise_fraction=1.,  # noise is reduced to g_noise_fraction at largest distance over a distance determined by g_plateau_fraction.
                 debug=False,
                 verbose=False):
        self.src = source
        self.g_ascii_file = g_ascii_file
        self.g_match = g_match
        self.g_scaled_file = g_scaled_file
        self.g_plateau_fraction = g_plateau_fraction
        self.g_noise_fraction = g_noise_fraction
        # --- Note: The following two parameters are obtained from the pipeline log!
        self.geometry = None
        self.x_particle_method = None
        # ---
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
        label = 'SolventMatching'
        param = {'g_ascii_file': self.g_ascii_file,
                 'g_match': self.g_match,
                 'g_scaled_file': self.g_scaled_file,
                 'g_plateau_fraction': self.g_plateau_fraction,
                 'g_noise_fraction': self.g_noise_fraction,
                 # --- we keep the following two entries for log purposes
                 'geometry': self.geometry,
                 'x_particle_method': self.x_particle_method}
        meta[label] = param
        return meta

    def next(self):
        """ Self-consistent solvent matching, implemented as a Python
        generator.  Implementation follows <lsz/shell-sc-solv-match.py>.
        """
        for obj in self.src.next():
            assert isinstance(obj, base.Container)

            if self.g_scaled_file is not None:
                # --- read g_scaled and rho from previous calculation ---
                reader = hdf5.H5Reader(filename=self.g_scaled_file)
                for frm in reader.next():
                    obj_g_scaled = frm
                    break
                del reader
                g_dict = obj_g_scaled.get_data(base.loc_solv_match + '/g_scaled')
                rho_dict = obj_g_scaled.get_data(base.loc_solv_match + '/rho')

            else:
                # --- compute g_scaled and rho ---

                # obtain information from the pipeline log
                dr = obj.query_meta('histograms/histogram/dr')
                assert (dr is not None)
                # ---
                self.geometry = obj.get_geometry()
                assert (self.geometry is not None)
                geometry_param = obj.query_meta(self.geometry)
                assert (geometry_param is not None)
                # ---
                virtual_param = obj.query_meta('AddVirtualParticles')
                if (virtual_param is not None):
                    self.x_particle_method = virtual_param['method']
                    xrho = virtual_param['xRho']

                # --- obtain the shell volume from the pipeline log
                if (self.geometry in ['Sphere', 'Cuboid', 'Ellipsoid']):
                    V_shell = geometry_param['shell_volume']
                    VSqr_shell = V_shell ** 2
                elif (self.geometry == 'ReferenceStructure' or self.geometry == 'MultiReferenceStructure'):
                    # V_shell is determined below
                    V_shell = None
                else:
                    raise NotImplementedError('Geometry ' + self.geometry +
                                              'not implemented for self-consistent solvent matching')

                # --- read and prepare g-function for matching
                g_header = (rdf.readHeader(self.g_ascii_file)).rstrip('\n').split()
                assert (self.g_match in g_header)
                _g_el_set = set([])
                for item in g_header:
                    if (item == '#'):
                        continue
                    pair = item.split(',')
                    _g_el_set.add(pair[0])
                    _g_el_set.add(pair[1])  # obsolete
                g_elements = sorted(list(_g_el_set))
                # ---
                g_table_0 = np.loadtxt(self.g_ascii_file)

                # TODO: Assert that histograms and rdfs have same bin size. Else, generate new rdf by interpolation.
                g_dr = (g_table_0[1:, 0] - g_table_0[:-1, 0]).mean()
                # print g_dr
                # Tapers noise for self.g_noise_fraction<1. Determines and set ginfty in last bins.
                g_table_0_smooth = rdf.smooth(g_table_0, g_dr, self.g_plateau_fraction, self.g_noise_fraction, verb=False)

#                 np.savetxt("g_table_0_smooth.dat", g_table_0_smooth)
                if (self.debug):
                    obj.put_data(base.loc_solv_match + '/g_table_0_smooth', g_table_0_smooth)

                g_table_0 = g_table_0_smooth

                _radii = obj.get_data(base.loc_histograms + '/radii')
                # Extend rdf in distance AFTER noise tapering, where rdf values at largest distance are set to ginfty.
                if _radii.shape[0] > g_table_0.shape[0]:
                    new_g_table = np.zeros((_radii.shape[0], g_table_0.shape[1]))
                    new_g_table[:g_table_0.shape[0], :] = g_table_0
                    new_g_table[:, 0] = _radii
                    tmp = g_table_0[-1, 1:]
                    new_g_table[g_table_0.shape[0]:, 1:] = tmp[np.newaxis, :]
                    g_table_0 = new_g_table
                    # np.savetxt("g_table_0_smooth_extended.dat", new_g_table)
                    if (self.debug):
                        obj.put_data(base.loc_solv_match + '/g_table_0_smooth_extended', new_g_table)

                # if do_g_extension:
                #     g_dr_0 = g_table_0[-1, 0] - g_table_0[-2, 0]
                #     g_nr_0 = g_table_0.shape[0]
                #     g_nrow = g_extension_factor * g_nr_0
                #     g_ncol = g_table_0.shape[1]
                #     g_table = np.zeros((g_nrow, g_ncol))
                #     g_table[0:g_nr_0, :] = g_table_0[0:g_nr_0, :]
                #     for idx in range(g_nr_0, g_nrow):
                #         g_table[idx, 0] = g_table[idx - 1, 0] + g_dr_0
                #         g_table[idx, 1:] = g_table[idx - 1, 1:]
                # else:
                #     g_table = g_table_0
                g_table = g_table_0
                # ---
                assert (len(g_header) == g_table.shape[1])
                g_idx = g_header.index(self.g_match)
                g_org = g_table[:, [0, g_idx]]
                if (self.debug):
                    obj.put_data(base.loc_solv_match + '/g_org', g_org)
                rho_g_org = g_org[0, 1]  # rho value stored at [0,1] (code by JK)
                # --- split g_table into a dict holding individual arrays
                g_dict = {}
                g_dict['radii'] = g_table[:, 0]
                for i in range(1, len(g_header)):
                    g_dict[g_header[i]] = g_table[:, i]

                # --- calculate particle and density of the matching solvent
                # get_shell also merges virtual particles X1 and X2
                shell = selection.get_shell(obj)
                # --- multiref: set properly (volume-weighted) averaged shell H_{xx}(r)
                # if (virtual_param is not None):
                if (virtual_param is not None and self.geometry == 'MultiReferenceStructure'):
                    shell.put_data(base.loc_histograms + "/X,X", obj.get_data(base.loc_shell_Hxx + "/X.s,X.s"))

                # --- determine V_shell and VSqr_shell for the reference and multiref structure case
                #  JK: Can/should be moved to Average filter?
                if (self.geometry == 'ReferenceStructure' or self.geometry == 'MultiReferenceStructure'):
                    nx = (shell.get_data(base.loc_nr_particles + '/X')).mean()
                    V_shell = nx / xrho
                    VSqr_shell = V_shell ** 2
                    if self.geometry == 'MultiReferenceStructure':
                        nxSqr = ((shell.get_data(base.loc_nr_particles + '/X')) ** 2).mean()
                        VSqr_shell = nxSqr / xrho ** 2
                # ---
                # print "###", self.g_match, shell.get_keys(base.loc_histograms)
                assert (self.g_match in shell.get_keys(base.loc_histograms))
                pair = self.g_match.split(',')
                assert (pair[0] == pair[1])
                assert (pair[0] in shell.get_keys(base.loc_nr_particles))
                # print shell.particles[pair[0]]
                n_match_avg = (shell.get_data(base.loc_nr_particles + '/' + pair[0])).mean()
                rho_match = n_match_avg / V_shell
                # JK: Should we instead use <n_i/V_i> averaged over frames for multiref??

                # Use SciPy interpolator object to operate on the
                # reference g function.  Warning: Linear interpolation!
                g_int = sint.interp1d(g_org[:, 0], g_org[:, 1])

                # --- solvent-matching calculation
                _radii = obj.get_data(base.loc_histograms + '/radii')
                pShell = np.zeros_like(_radii)
                H = np.zeros_like(_radii)
                gAct = np.zeros_like(_radii)
                # ---
                if (self.geometry == 'Sphere') and (self.x_particle_method is None):
                    R = geometry_param['radius']
                    sw = geometry_param['shell_width']
                    for i, r in enumerate(_radii):
                        pShell[i] = rdf.PSh(R - sw, R, r)
                        H[i] = pShell[i] * g_int(_radii[i])
                else:
                    histgrms = shell.get_data(base.loc_histograms)
                    pShell = histgrms['X,X'].copy()
                    pShell /= pShell.sum()
                    pShell /= dr
                    for i, r in enumerate(_radii):
                        if (pShell[i] > 0.0):
                            gAct[i] /= pShell[i]
                        else:
                            gAct[i] = 0.0
                        if (_radii[i] < g_dict['radii'][0]) or (_radii[i] >= g_dict['radii'][-1]):
                            H[i] = 0.0
                        else:
                            H[i] = pShell[i] * g_int(_radii[i])
                # ---
                pre_factor = rho_match ** 2 * VSqr_shell * dr / 2.
                # print "### pre_factor =", pre_factor
                H[:] *= pre_factor
                histo = shell.get_data(base.loc_histograms + '/' + self.g_match)
                scale_factor = np.sum(histo[:] * H[:]) / np.sum(H[:] ** 2)
                # print "###  scale_factor =", scale_factor
                obj.put_data(base.loc_solv_match + '/scale_factor', scale_factor)
                if (self.debug):
                    obj.put_data(base.loc_solv_match + '/pre_factor', pre_factor)
                    obj.put_data(base.loc_solv_match + '/scale_factor', scale_factor)
                    obj.put_data(base.loc_solv_match + '/histo', histo)
                    obj.put_data(base.loc_solv_match + '/pShell', pShell)
                    obj.put_data(base.loc_solv_match + '/H', H)
                # ---
                H *= scale_factor
                gAct /= scale_factor

                if (self.debug):
                    obj.put_data(base.loc_solv_match + '/H_scaled', H)
                    obj.put_data(base.loc_solv_match + '/gAct', gAct)

                # ---
                rho_dict = {}
                for name in g_elements:
                    avg = (shell.get_data(base.loc_nr_particles + '/' + name)).mean()
                    rho_dict[name] = avg / V_shell

                if (self.debug):
                    obj.put_data(base.loc_solv_match + '/rho_g_org', rho_g_org)
                    obj.put_data(base.loc_solv_match + '/rho_match', rho_match)

                # --- Patch zeroeth elements of g arrays with the density,
                # --> Do we really want to keep this convention?
                for key in rho_dict:
                    pair = key + ',' + key
                    assert (pair in g_dict)
                    (g_dict[pair])[0] = rho_dict[key]

                if (self.debug):
                    obj.put_data(base.loc_solv_match + '/g_original', g_dict)

                # --- final rescaled g functions used by delta_h
                for key in g_dict:
                    if (key == 'radii'):
                        continue
                    else:
                        (g_dict[key])[1:] *= scale_factor

            obj.put_data(base.loc_solv_match + '/g_scaled', g_dict)
            obj.put_data(base.loc_solv_match + '/rho', rho_dict)
            obj.put_meta(self.get_meta())
            if self.verb:
                print "Solvent.next() :", obj.i
            yield obj
