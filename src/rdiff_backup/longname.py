# Copyright 2005 Ben Escoto
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
"""Handle long filenames

rdiff-backup sometimes wants to write filenames longer than allowed by
the destination directory.  This can happen in 3 ways:

1)  Because the destination directory has a low maximum length limit.
2)  When the source directory has a filename close to the limit, so
    that its increments would be above the limit.
3)  When quoting is enabled, so that even the mirror filenames are too
    long.

When rdiff-backup would otherwise write a file whose name is too long,
instead it either skips the operation altogether (for non-regular
files), or writes the data to a unique file in the
rdiff-backup-data/long-filename directory.  This file will have an
arbitrary basename, but if it's an increment the suffix will be the
same.  The name will be recorded in the mirror_metadata so we can find
it later.

"""

import types
import errno
from . import log, Globals, restore, rpath, FilenameMapping, regress

long_name_dir = b"long_filename_data"
rootrp = None




# ------------------------------------------------------------------
# These functions used mainly for backing up

# integer number of next free prefix.  Names will be created from
# integers consecutively like '1', '2', and so on.
free_name_counter = None

# Filename which holds the next available free name in it
counter_filename = b"next_free"


def get_next_free():


	If make_dir is True, make any parent directories to assure that
	file is really too long, and not just in directories that don't exist.

	"""


def get_mirror_rp(mirror_base, mirror_rorp):
    """Get the mirror_rp for reading a regular file

	This will just be in the mirror_base, unless rorp has an alt
	mirror name specified.  Use new_rorp, unless it is None or empty,
	and mirror_rorp exists.

	"""




	To test inc_rp, pad incbase with 50 random (non-quoted) characters
	and see if that raises an error.

	"""



# ------------------------------------------------------------------
# The following section is for restoring

# This holds a dictionary {incbase: inclist}.  The keys are increment
# bases like '1' or '23', and the values are lists containing the
# associated increments.
restore_inc_cache = None


def set_restore_cache():
    """Initialize restore_inc_cache based on long filename dir"""
    global restore_inc_cache
    restore_inc_cache = {}
    root_rf = restore.RestoreFile(get_long_rp(), get_long_rp(), [])
    for incbase_rp, inclist in root_rf.yield_inc_complexes(get_long_rp()):
        restore_inc_cache[incbase_rp.index[-1]] = inclist


def get_inclist(inc_base_name):


def update_rf(rf, rorp, mirror_root):


def update_regressfile(rf, rorp, mirror_root):

