"""Capriqorn filter library <postproc_filter_dummy.py>

This file is part of the capriqorn package.  See README.rst,
LICENSE.txt, and the documentation for details.
"""

import numpy as np

from cadishi import base
from cadishi import util
from cadishi import dict_util


def scaleFactorXX(nx, xrho):
    """
    Scale factor for $H_{xx}(r)$ is given by one over normalizaiton constant 2/($N_x^2-N_x$)
    times the volume squared $(N_x/\rho_x)^2$. We addtionally use the factor 0.5 here,
    canceling with the factor 2 in the normalization constant,
    because all histograms are multiplied by two in the DeltaH filter.
    """
    return (nx / xrho ** 2 / (nx - 1.))

def scaleFactorX1X2(nx1, nx2, xrho):
    """
    For the 'lattice' virtual particle method, the normalization constant is
    given by nx1*nx2 and the total number of particles by nx1+nx2.
    We addtionally use the factor 0.5 here because all histograms are
    multiplied by two in the DeltaH filter.
    """
    return 0.5 * ((nx1 + nx2) / xrho) ** 2 / float(nx1 * nx2)

def scaleVirtualHistograms(frm):
    """
    When using the MultiReferenceStructure filter, histograms containing  virtual particles
    have to be properly scaled before averaging. The reason beeing that the volumes of the
    observation volumes vary for each frame. This scaling should also work when using
    a single reference structure, where the volume is constant for each frame.

    To facilitate solvent matching, we properly scale the X,X histograms of the shell
    and save them separately from the original histograms for later use.

    Precondition:
        o Each frames contains a single histogram only (sample=1 in histograms.yaml),
          because the volume varies for each frame.

    Scale factors for the 'gas' and 'lattice' methods are different because
    in the 'lattice' method we evaluate distances between two separate sets
    of particles (called X1 and X2).

    Note that because of the scaling applied here the norms of the cross, core, and
    shell histograms are no longer meaningfull. Only the norm of the full histogram is.
    """

    virtual_param = frm.query_meta('VirtualParticles')
    if (virtual_param is not None):
        method = virtual_param['method']
        xrho = virtual_param['x_density']
    else:
        return frm
    geom = frm.get_geometry()
    meta = frm.query_meta(geom)

    if method == 'gas':
        nrPart = frm.get_data(base.loc_nr_particles)
        nx = nrPart['X'][0]
        # print " nx =", nx
        if meta['shell_width'] > 0:
            shell_Hxx = frm.get_data(base.loc_histograms + "/X.s,X.s")
            frm.put_data(base.loc_shell_Hxx, {'X.s,X.s':shell_Hxx})
            nXs = (frm.get_data(base.loc_nr_particles))['X.s'][0]
            shell_Hxx = frm.get_data(base.loc_shell_Hxx)
            dict_util.scale_values(shell_Hxx, scaleFactorXX(nXs, xrho))

        histgrms = frm.get_data(base.loc_histograms)
        elements = util.get_elements(histgrms.keys())
        # The scaling is the same for core, cross, shell, and full, because
        # full is given by a linear combination of core, cross, and shell.
        # We identify $H_{ix}(r)$ and $H_{xx}(r)$  by counting 'X' in the keys
        # (only works if there is no species a name with multiple 'X').
        for key in frm.get_keys(base.loc_histograms):
            XCounter = key.count('X')
            if XCounter == 1:
                histgrms[key] /= xrho
            elif XCounter == 2:
                # print histgrms[key].sum(), (nx**2-nx)
                histgrms[key] *= scaleFactorXX(nx, xrho)
        frm.put_data(base.loc_histograms, histgrms)
    elif method == 'lattice':
        nrPart = frm.get_data(base.loc_nr_particles)
        nx1 = nrPart['X1'][0] + nrPart['X1.s'][0]
        nx2 = nrPart['X2'][0] + nrPart['X2.s'][0]
        nx = nx1 + nx2

        if meta['shell_width'] > 0:
            shell_Hxx = frm.get_data(base.loc_histograms + "/X1.s,X2.s")
            frm.put_data(base.loc_shell_Hxx, {'X.s,X.s':shell_Hxx})
            nXs1 = nrPart['X1.s'][0]
            nXs2 = nrPart['X2.s'][0]
            shell_Hxx = frm.get_data(base.loc_shell_Hxx)
            # shell_Hxx is normalized in the Solvent filter. A constant scale factor
            # does not have any influence.
            dict_util.scale_values(shell_Hxx, scaleFactorX1X2(nXs1, nXs2, xrho))

        histgrms = frm.get_data(base.loc_histograms)
        elements = util.get_elements(histgrms.keys())
        for key in frm.get_keys(base.loc_histograms):
            XCounter = key.count('X')
            if XCounter == 1:
                histgrms[key] /= xrho
            elif XCounter == 2:
                histgrms[key] *= scaleFactorX1X2(nx1, nx2, xrho)
        frm.put_data(base.loc_histograms, histgrms)
    return frm


class Average(base.Filter):
    """a filter that averages over histograms"""
    _depends = []
    _conflicts = []

    def __init__(self, n_avg=1, factor=1.0, source=-1, all=False, verbose=False):
        # average over n_avg frames
        self.n_avg = n_avg
        # alternatively: average over all frames
        self.all = all
        # custom factor applied when averaging
        self.factor = factor
        self.src = source
        self.verb = verbose
        self.count = 0
        self._depends.extend(super(base.Filter, self)._depends)
        self._conflicts.extend(super(base.Filter, self)._conflicts)

    def apply_rescaling(self, frm_in, frm_out, n_avg, virtual_param):
        """Apply rescaling and averaging operations. Method factored out from next()."""
        frm_out.i = frm_in.i
        # --- perform averaging on histograms
        val = np.float_(self.factor) / np.float_(n_avg)
        # --- rescale distance histograms
        if frm_out.has_key(base.loc_histograms):
            X = frm_out.get_data(base.loc_histograms)
            dict_util.scale_values(X, val)
        # --- multiref: rescale shell XX histogram
        if (virtual_param is not None and self.geometry == 'MultiReferenceStructure'):
            if frm_out.has_key(base.loc_shell_Hxx):
                X = frm_out.get_data(base.loc_shell_Hxx)
                dict_util.scale_values(X, val)
        # --- rescale length histograms
        if frm_out.has_key(base.loc_len_histograms):
            X = frm_out.get_data(base.loc_len_histograms)
            dict_util.scale_values(X, val)
        # ---
        frm_out.put_data('log', frm_in.get_data('log'))
        frm_out.put_meta(self.get_meta())

    def get_meta(self):
        """
        return information on the present filter,
        ready to be added to a frame frm_inect's list of
        pipeline meta information
        """
        meta = {}
        label = 'Average'
        param = {'n_avg': self.n_avg, 'factor': self.factor}
        meta[label] = param
        return meta

    def next(self):
        frm_out = base.Container()
        for frm_in in self.src.next():
            self.geometry = frm_in.get_geometry()
            # --- multiref: scale histograms containing virtual particles
            virtual_param = frm_in.query_meta('VirtualParticles')
            if (virtual_param is not None and self.geometry == 'MultiReferenceStructure'):
                frm_in = scaleVirtualHistograms(frm_in)
            # --- take into account the histogram sample parameter when averaging
            if (self.count == 0):
                histo_par = util.search_pipeline('histograms', frm_in.get_meta())
                if (histo_par is not None) and (len(histo_par) > 0):
                    histo_sample = histo_par['histogram']['sum']
                    self.factor = self.factor / float(histo_sample)
            # --- sum distance histograms
            if not frm_out.has_key(base.loc_histograms + '/radii'):
                frm_out.put_data(base.loc_histograms + '/radii',
                                 frm_in.get_data(base.loc_histograms + '/radii'))
            X = frm_out.get_data(base.loc_histograms)
            Y = frm_in.get_data(base.loc_histograms)
            dict_util.sum_values(X, Y)
            # --- sum shell H_xx(r)
            if (virtual_param is not None and self.geometry == 'MultiReferenceStructure'):
                if not frm_out.has_key(base.loc_shell_Hxx):
                    frm_out.put_data(base.loc_shell_Hxx, frm_in.get_data(base.loc_shell_Hxx))
                X = frm_out.get_data(base.loc_shell_Hxx)
                Y = frm_in.get_data(base.loc_shell_Hxx)
                dict_util.sum_values(X, Y)
            # --- sum length histograms (only present with Sphere geometry)
            if frm_in.has_key(base.loc_len_histograms):
                if not frm_out.has_key(base.loc_len_histograms + '/radii'):
                    frm_out.put_data(base.loc_len_histograms + '/radii',
                                     frm_in.get_data(base.loc_len_histograms + '/radii'))
                X = frm_out.get_data(base.loc_len_histograms)
                Y = frm_in.get_data(base.loc_len_histograms)
                dict_util.sum_values(X, Y)
            # --- append particle numbers
            if frm_in.has_key(base.loc_nr_particles):
                frm_out.append_data(frm_in, base.loc_nr_particles)
            # --- append periodic box volumes
            if frm_in.has_key(base.loc_volumes):
                frm_out.append_data(frm_in, base.loc_volumes)
            # ---
            self.count += 1
            # deliver a frame averaged over n_avg frames
            if (not self.all) and (self.count % self.n_avg == 0):
                self.apply_rescaling(frm_in, frm_out, self.n_avg, virtual_param)
                if self.verb:
                    print "Average.next() :", frm_in.i
                yield frm_out
                del frm_out
                frm_out = base.Container()
        # rescale and deliver a single frame if averaging over all frames is desired
        if self.all:
            self.apply_rescaling(frm_in, frm_out, self.count, virtual_param)
            if self.verb:
                print "Average.next() :", frm_in.i
            yield frm_out
