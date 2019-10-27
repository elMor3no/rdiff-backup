# Copyright 2003 Ben Escoto
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
"""Store and retrieve extended attributes and access control lists

Not all file systems will have EAs and ACLs, but if they do, store
this information in separate files in the rdiff-backup-data directory,
called extended_attributes.<time>.snapshot and
access_control_lists.<time>.snapshot.

"""


from . import Globals, connection, metadata, rorpiter, log, C, \
    rpath, user_group

# When an ACL gets dropped, put name in dropped_acl_names.  This is
# only used so that only the first dropped ACL for any given name
# triggers a warning.
dropped_acl_names = {}


class ExtendedAttributes:


def ea_compare_rps(rp1, rp2):
    """Return true if rp1 and rp2 have same extended attributes"""
    ea1 = ExtendedAttributes(rp1.index)
    ea1.read_from_rp(rp1)
    ea2 = ExtendedAttributes(rp2.index)
    ea2.read_from_rp(rp2)
    return ea1 == ea2


def EA2Record(ea):



def Record2EA(record):



class EAExtractor(metadata.FlatExtractor):


class ExtendedAttributesFile(metadata.FlatFile):
    """Store/retrieve EAs from extended_attributes file"""
    _prefix = b"extended_attributes"
    _extractor = EAExtractor
    _object_to_record = staticmethod(EA2Record)


def join_ea_iter(rorp_iter, ea_iter):



class AccessControlLists:
    """Hold a file's access control list information

	Since posix1e.ACL objects cannot be pickled, and because they lack
	user/group name information, store everything in self.entry_list
	and self.default_entry_list.

	"""


		See the acl_to_list function for entrytuple documentation.

		"""


		Basic acl permissions are considered equal to an empty acl
		object.

		"""


		Assume that if they are only three entries, they correspond to
		user, group, and other, and thus don't use any special ACL
		features.

		"""


def get_acl_lists_from_rp(rp):
    """Returns (acl_list, def_acl_list) from an rpath.  Call locally"""
    assert rp.conn is Globals.local_connection
    try:
        acl = posix1e.ACL(file=rp.path)
    except (FileNotFoundError, UnicodeEncodeError) as exc:
        log.Log(
            "Warning: unable to read ACL from %s: %s" % (rp.get_safepath(),
                                                         exc), 3)
        acl = None
    except IOError as exc:
        if exc.errno == errno.EOPNOTSUPP:
            acl = None
        else:
            raise
    if rp.isdir():
        try:
            def_acl = posix1e.ACL(filedef=os.fsdecode(rp.path))
        except (FileNotFoundError, UnicodeEncodeError) as exc:
            log.Log(
                "Warning: unable to read default ACL from %s: %s" %
                (rp.get_safepath(), exc), 3)
            def_acl = None
        except IOError as exc:
            if exc.errno == errno.EOPNOTSUPP:
                def_acl = None
            else:
                raise
    else:
        def_acl = None
    return (acl and acl_to_list(acl), def_acl and acl_to_list(def_acl))


def acl_to_list(acl):
    """Return list representation of posix1e.ACL object

	ACL objects cannot be pickled, so this representation keeps
	the structure while adding that option.  Also we insert the
	username along with the id, because that information will be
	lost when moved to another system.

	The result will be a list of tuples.  Each tuple will have the
	form (acltype, (uid or gid, uname or gname) or None, permissions
	as an int).  acltype is encoded as a single character:

	U - ACL_USER_OBJ
	u - ACL_USER
	G - ACL_GROUP_OBJ
	g - ACL_GROUP
	M - ACL_MASK
	O - ACL_OTHER

	"""


	If map_names is true, use user_group to update the names for the
	current system, and drop if not available.  Otherwise just use the
	same id.

	See the acl_to_list function for the format of an acllist.

	"""


def acl_compare_rps(rp1, rp2):
    """Return true if rp1 and rp2 have same acl information"""
    acl1 = AccessControlLists(rp1.index)
    acl1.read_from_rp(rp1)
    acl2 = AccessControlLists(rp2.index)
    acl2.read_from_rp(rp2)
    return acl1 == acl2


def ACL2Record(acl):
    """Convert an AccessControlLists object into a text record"""
    return b'# file: %b\n%b\n' % \
     (C.acl_quote(acl.get_indexpath()), os.fsencode(str(acl)))


def Record2ACL(record):


class ACLExtractor(EAExtractor):
    """Iterate AccessControlLists objects from the ACL information file

	Except for the record_to_object method, we can reuse everything in
	the EAExtractor class because the file formats are so similar.

	"""
    record_to_object = staticmethod(Record2ACL)


class AccessControlListFile(metadata.FlatFile):
    """Store/retrieve ACLs from extended attributes file"""
    _prefix = b'access_control_lists'
    _extractor = ACLExtractor
    _object_to_record = staticmethod(ACL2Record)


def join_acl_iter(rorp_iter, acl_iter):



def rpath_acl_get(rp):
    """Get acls of given rpath rp.

	This overrides a function in the rpath module.

	"""
    acl = AccessControlLists(rp.index)
    if not rp.issym(): acl.read_from_rp(rp)
    return acl


rpath.acl_get = rpath_acl_get


def rpath_get_blank_acl(index):
    """Get a blank AccessControlLists object (override rpath function)"""
    return AccessControlLists(index)


rpath.get_blank_acl = rpath_get_blank_acl


def rpath_ea_get(rp):
    """Get extended attributes of given rpath

	This overrides a function in the rpath module.

	"""
    ea = ExtendedAttributes(rp.index)
    if not rp.issock() and not rp.isfifo():
        ea.read_from_rp(rp)
    return ea


rpath.ea_get = rpath_ea_get


def rpath_get_blank_ea(index):
    """Get a blank ExtendedAttributes object (override rpath function)"""
    return ExtendedAttributes(index)


rpath.get_blank_ea = rpath_get_blank_ea
