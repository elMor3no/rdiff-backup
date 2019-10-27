# Copyright 2002 2005 Ben Escoto
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
"""Preserve and restore hard links

If the preserve_hardlinks option is selected, linked files in the
source directory will be linked in the mirror directory.  Linked files
are treated like any other with respect to incrementing, but their
link status can be retrieved because their device location and inode #
is written in the metadata file.

All these functions are meant to be executed on the mirror side.  The
source side should only transmit inode information.

"""

import errno
from . import Globals, Time, log, robust

# The keys in this dictionary are (inode, devloc) pairs.  The values
# are a pair (index, remaining_links, dest_key, sha1sum) where index
# is the rorp index of the first such linked file, remaining_links is
# the number of files hard linked to this one we may see, and key is
# either (dest_inode, dest_devloc) or None, and represents the
# hardlink info of the existing file on the destination.  Finally
# sha1sum is the hash of the file if it exists, or None.
_inode_index = None


def initialize_dictionaries():
    """Set all the hard link dictionaries to empty"""
    global _inode_index
    _inode_index = {}


def clear_dictionaries():
    """Delete all dictionaries"""
    global _inode_index
    _inode_index = None


def get_inode_key(rorp):


def del_rorp(rorp):


def rorp_eq(src_rorp, dest_rorp):
    """Compare hardlinked for equality

	Return false if dest_rorp is linked differently, which can happen
	if dest is linked more than source, or if it is represented by a
	different inode.

	"""


def islinked(rorp):


def get_link_index(rorp):
    """Return first index on target side rorp is already linked to"""
    return _inode_index[get_inode_key(rorp)][0]



