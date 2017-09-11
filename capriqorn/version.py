# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
# 
# Capriqorn --- CAlculation of P(R) and I(Q) Of macRomolcules in solutioN 
#
# Copyright (c) Juergen Koefinger, Klaus Reuter, and contributors.
# See the file AUTHORS.rst for the full list of contributors.
#
# Released under the GNU Public Licence, v2 or any higher version, see the file LICENSE.txt.

# We handle version information in a single file as is commonly done, see e.g.
# https://packaging.python.org/single_source_version/#single-sourcing-the-version

# The 'ver' tuple is read by the setup.py, conf.py of the Sphinx documentation
# system and __init__.py of the package.
ver = (1, 0, 0)


def get_version_string():
    """Return the full version number."""
    return '.'.join(map(str, ver))


def get_short_version_string():
    """Return the version number without the patchlevel."""
    return '.'.join(map(str, ver[:-1]))


def get_printable_version_string():
    version_string = " Capriqorn " + get_version_string()
    try:
        from . import githash
    except:
        pass
    else:
        version_string += " (git: " + githash.human_readable + ")"
    return version_string
