"""Capriqorn geometry selection library.

The core, shell, full selection routines are implemented here, as
well as the the functionality to merge virtual particles.
"""
# This file is part of the capriqorn package.  See README.rst,
# LICENSE.txt, and the documentation for details.

import numpy as np

from cadishi import base
from cadishi import util
from cadishi import dict_util
from ..postproc.filter.strip_virtual_particles import blacklist


def get_core(frm_in):
    """
    Selects the core parts of a base.Container() instance,
    and returns them inside a new base.Container() instance.
    """
    frm_out = base.Container()
    # ---
    frm_out.i = frm_in.i
    # --- extend pipeline_log
    frm_out.put_data('log', frm_in.get_data('log'))
    log_entry = {'get_core': True}
    frm_out.put_meta(log_entry)
    # --- filter particle numbers
    for key in sorted(frm_in.get_keys(base.loc_nr_particles)):
        if key.endswith('.s'):
            continue
        frm_out.put_data(base.loc_nr_particles + '/' + key,
                         frm_in.get_data(base.loc_nr_particles + '/' + key))
    # --- filter histogram data
    for key in sorted(frm_in.get_keys(base.loc_histograms)):
        if (key != 'radii'):
            pair = key.split(',')
            if (pair[0].endswith('.s') or pair[1].endswith('.s')):
                continue
        frm_out.put_data(base.loc_histograms + '/' + key,
                         frm_in.get_data(base.loc_histograms + '/' + key))
    # ---
    merge_virtual_particles(frm_out)
    # ---
    return frm_out


def get_shell(frm_in):
    """
    Selects the shell parts of a base.Container() instance,
    and returns them inside a new base.Container() instance.
    """
    frm_out = base.Container()
    # ---
    frm_out.i = frm_in.i
    # --- extend pipeline_log
    frm_out.put_data('log', frm_in.get_data('log'))
    log_entry = {'get_shell': True}
    frm_out.put_meta(log_entry)
    # --- filter particle numbers
    for key in sorted(frm_in.get_keys(base.loc_nr_particles)):
        if key.endswith('.s'):
            # strip off the trailing shell identifier
            frm_out.put_data(base.loc_nr_particles + '/' + key[:-2],
                             frm_in.get_data(base.loc_nr_particles + '/' + key))
        elif (key == 'frame'):
            frm_out.put_data(base.loc_nr_particles + '/' + key,
                             frm_in.get_data(base.loc_nr_particles + '/' + key))
    # --- filter histogram data
    for key in sorted(frm_in.get_keys(base.loc_histograms)):
        pair = key.split(',')
        if (pair[0].endswith('.s') and pair[1].endswith('.s')):
            # strip off the trailing shell identifiers
            key_new = (pair[0])[:-2] + ',' + (pair[1])[:-2]
            frm_out.put_data(base.loc_histograms + '/' + key_new,
                             frm_in.get_data(base.loc_histograms + '/' + key))
        elif (key == 'radii'):
            frm_out.put_data(base.loc_histograms + '/' + key,
                             frm_in.get_data(base.loc_histograms + '/' + key))
    # ---
    merge_virtual_particles(frm_out)
    # ---
    return frm_out


def get_cross(frm_in):
    """
    Selects the cross parts of a base.Container() instance,
    and returns them inside a new base.Container() instance.
    """
    frm_out = base.Container()
    # ---
    frm_out.i = frm_in.i
    # --- extend pipeline_log
    frm_out.put_data('log', frm_in.get_data('log'))
    log_entry = {'get_cross': True}
    frm_out.put_meta(log_entry)
    # Note: particle numbers do not make sense for cross
    for key in sorted(frm_in.get_keys(base.loc_histograms)):
        if (key != 'radii'):
            pair = key.split(',')
            if (pair[0].endswith('.s') and pair[1].endswith('.s')) or \
               (not pair[0].endswith('.s') and not pair[1].endswith('.s')):
                continue
        frm_out.put_data(base.loc_histograms + '/' + key,
                         frm_in.get_data(base.loc_histograms + '/' + key))
    # ---
    merge_virtual_particles(frm_out)
    # ---
    return frm_out


def get_full(frm_in):
    """
    Selects the core, shell, cross parts of a base.Container() instance,
    and returns them inside a new base.Container() instance in a combined way.
    """
    #######################
    # if there's no shell (shell_width<0) then the histogram is already the full histogram
    geom = frm_in.get_geometry()
    meta = frm_in.query_meta(geom)
    if meta['shell_width'] < 0:
        return frm_in
    #######################
    frm_out = base.Container()
    # ---
    frm_out.i = frm_in.i
    # --- extend pipeline_log
    frm_out.put_data('log', frm_in.get_data('log'))
    log_entry = {'get_full': True}
    frm_out.put_meta(log_entry)
    # --- construct the full set from the divided sets
    frm_out_core = get_core(frm_in)
    frm_out_shell = get_shell(frm_in)
    frm_out_cross = get_cross(frm_in)
    # --- sum up particle numbers
    frm_out.put_data(base.loc_nr_particles,  # include radii
                     frm_out_core.get_data(base.loc_nr_particles))
    X = frm_out.get_data(base.loc_nr_particles)
    Y = frm_out_shell.get_data(base.loc_nr_particles)
    dict_util.sum_values(X, Y)  # semantics: X += Y
    # --- sum up histogram vectors
    frm_out.put_data(base.loc_histograms,  # include radii
                     frm_out_core.get_data(base.loc_histograms))
    X = frm_out.get_data(base.loc_histograms)
    Y = frm_out_shell.get_data(base.loc_histograms)
    dict_util.sum_values(X, Y)  # semantics: X += Y
    # --- sum up cross histograms explicitly due to key handling
    for (key, Y) in (frm_out_cross.get_data(base.loc_histograms)).items():
        if (key == 'radii'):
            continue
        else:
            pair = key.split(',')
            for idx in [0, 1]:
                if pair[idx].endswith('.s'):
                    pair[idx] = (pair[idx])[:-2]
            key_new = pair[0] + ',' + pair[1]
            X = frm_out.get_data(base.loc_histograms + '/' + key_new)
            X += Y
    # ---
    merge_virtual_particles(frm_out)
    # ---
    return frm_out


def merge_virtual_particles(frm):
    """
    Merges the virtual particle species X1,X2 in a base.Container() instance.
    Modifies the base.Container() instance in-place.
    """
    assert isinstance(frm, base.Container)
    # --- sum up the distance histograms
    if frm.has_key(base.loc_histograms):
        histgrms = frm.get_data(base.loc_histograms)
        for key in histgrms.keys():
            # Use StripVirtualParticles() earlier in the pipeline!
            assert (key not in blacklist)
        elements = util.get_elements(histgrms.keys())
        if ('X1' in elements) and ('X2' in elements):
            all_X1 = []
            all_X2 = []
            for key in histgrms.keys():
                if 'X1' in key:
                    all_X1.append(key)
                elif 'X2' in key:
                    all_X2.append(key)
            all_X1X2 = sorted(set(all_X1 + all_X2))
            for key in all_X1X2:
                key_new = key.replace('X1', 'X').replace('X2', 'X')
                # print "###", key, key_new
                if key_new not in histgrms.keys():
                    histgrms[key_new] = np.zeros_like(histgrms[key])
                histgrms[key_new] += histgrms[key]
                del histgrms[key]
    # --- sum up the particle number arrays
    if frm.has_key(base.loc_nr_particles):
        partnums = frm.get_data(base.loc_nr_particles)
        elements = util.get_elements(partnums.keys())
        if ('X1' in elements) and ('X2' in elements):
            X1 = partnums['X1']
            X2 = partnums['X2']
            X = X1 + X2
            partnums['X'] = X.copy()
            del X
            del partnums['X1']
            del partnums['X2']
    # --- sum up the length histogram arrays
    if frm.has_key(base.loc_len_histograms):
        lenhists = frm.get_data(base.loc_len_histograms)
        elements = util.get_elements(lenhists.keys())
        if ('X1' in elements) and ('X2' in elements):
            X1 = lenhists['X1']
            X2 = lenhists['X2']
            X = X1 + X2
            lenhists['X'] = X.copy()
            del X
            del lenhists['X1']
            del lenhists['X2']
