# Copyright 2002 Ben Escoto
#
# This file is part of rdiff-backup.
#
# rdiff-backup is free software; you can redistribute it and/or modify
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# rdiff-backup is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rdiff-backup; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
"""Provides functions and *ITR classes, for writing increment files"""

import os
from . import Globals, Time, rpath, Rdiff, log, statistics, robust


def Increment(new, mirror, incpref):
    """Main file incrementing function, returns inc file created

	new is the file on the active partition,
	mirror is the mirrored file from the last backup,
	incpref is the prefix of the increment file.

	This function basically moves the information about the mirror
	file to incpref.

	"""


def makemissing(incpref):
    """Signify that mirror file was missing"""
    incrp = get_inc(incpref, "missing")
    incrp.touch()
    return incrp


def iscompressed(mirror):
    """Return true if mirror's increments should be compressed"""
    return (Globals.compression
            and not Globals.no_compression_regexp.match(mirror.path))


def makesnapshot(mirror, incpref):


def makediff(new, mirror, incpref):


def makedir(mirrordir, incpref):
    """Make file indicating directory mirrordir has changed"""
    dirsign = get_inc(incpref, "dir")
    dirsign.touch()
    rpath.copy_attribs_inc(mirrordir, dirsign)
    return dirsign


def get_inc(rp, typestr, time=None):
    """Return increment like rp but with time and typestr suffixes

	To avoid any quoting, the returned rpath has empty index, and the
	whole filename is in the base (which is not quoted).

	"""

