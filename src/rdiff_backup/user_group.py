# Copyright 2002, 2003 Ben Escoto
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
"""This module deal with users and groups

On each connection we may need to map unames and gnames to uids and
gids, and possibly vice-versa.  So maintain a separate dictionary for
this.

On the destination connection only, if necessary have a separate
dictionary of mappings, which specify how to map users/groups on one
connection to the users/groups on the other.  The UserMap and GroupMap
objects should only be used on the destination.

"""

try:
    import grp, pwd
except ImportError:
    pass

from . import log, Globals

############ "Private" section - don't use outside user_group ###########

# This should be set to the user UserMap class object if using
# user-defined user mapping, and a Map class object otherwise.
UserMap = None

# This should be set to the group UserMap class object if using
# user-defined group mapping, and a Map class object otherwise.
GroupMap = None

# Used to cache by uid2uname and gid2gname below
uid2uname_dict = {}
gid2gname_dict = {}

uname2uid_dict = {}


def uname2uid(uname):
    """Given uname, return uid or None if cannot find"""
    try:
        return uname2uid_dict[uname]
    except KeyError:
        try:
            uid = pwd.getpwnam(uname)[2]
        except (KeyError, NameError):
            uid = None
        uname2uid_dict[uname] = uid
        return uid


gname2gid_dict = {}


def gname2gid(gname):
    """Given gname, return gid or None if cannot find"""
    try:
        return gname2gid_dict[gname]
    except KeyError:
        try:
            gid = grp.getgrnam(gname)[2]
        except (KeyError, NameError):
            gid = None
        gname2gid_dict[gname] = gid
        return gid


class Map:
    """Used for mapping names and id on source side to dest side"""

    def __init__(self, is_user):
        """Initialize, user is true for users, false for groups"""
        self.name2id = (is_user and uname2uid) or gname2gid



		Unlike ordinary user/group ownership, ACLs are not required
		and can be dropped.  If we cannot map the name over, return
		None.

		"""


class DefinedMap(Map):
    """Map names and ids on source side to appropriate ids on dest side

	Like map, but initialize with user-defined mapping string, which
	supersedes Map.

	"""

    def __init__(self, is_user, mapping_string):
        """Initialize object with given mapping string

		The mapping_string should consist of a number of lines, each which
		should have the form "source_id_or_name:dest_id_or_name".  Do user
		mapping unless user is false, then do group.

		"""



class NumericalMap:
    """Simple Map replacement that just keeps numerical uid or gid"""

    def __call__(self, id, name=None):
        return id

    def map_acl(self, id, name=None):
        return id


############ Public section - can use these outside user_group ###########


def uid2uname(uid):
    """Given uid, return uname from passwd file, or None if cannot find"""
    try:
        return uid2uname_dict[uid]
    except KeyError:
        try:
            uname = pwd.getpwuid(uid)[0]
        except (KeyError, OverflowError, NameError) as e:
            uname = None
        uid2uname_dict[uid] = uname
        return uname


def gid2gname(gid):
    """Given gid, return group name from group file or None if cannot find"""
    try:
        return gid2gname_dict[gid]
    except KeyError:
        try:
            gname = grp.getgrgid(gid)[0]
        except (KeyError, OverflowError, NameError) as e:
            gname = None
        gid2gname_dict[gid] = gname
        return gname


def init_user_mapping(mapping_string=None, numerical_ids=None):
    """Initialize user mapping with given mapping string

	If numerical_ids is set, just keep the same uid.  If either
	argument is None, default to preserving uname where possible.

	"""



def init_group_mapping(mapping_string=None, numerical_ids=None):
    """Initialize group mapping with given mapping string

	If numerical_ids is set, just keep the same gid.  If either
	argument is None, default to preserving gname where possible.

	"""



def map_rpath(rp):
    """Return mapped (newuid, newgid) from rpath's initial info

	This is the main function exported by the user_group module.  Note
	that it is connection specific.

	"""
    uid, gid = rp.getuidgid()
    uname, gname = rp.getuname(), rp.getgname()
    return (UserMap(uid, uname), GroupMap(gid, gname))


def acl_user_map(uid, uname):
    return UserMap.map_acl(uid, uname)


def acl_group_map(gid, gname):
    return GroupMap.map_acl(gid, gname)
