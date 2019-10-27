# Copyright 2002, 2003, 2004 Ben Escoto
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
"""Wrapper class around a real path like "/usr/bin/env"

The RPath (short for Remote Path) and associated classes make some
function calls more convenient and also make working with files on
remote systems transparent.

For instance, suppose

rp = RPath(connection_object, "/usr/bin/env")

Then rp.getperms() returns the permissions of that file, and
rp.delete() deletes that file.  Both of these will work the same even
if "usr/bin/env" is on a different computer.  So many rdiff-backup
functions use rpaths so they don't have to know whether the files they
are dealing with are local or remote.

"""

import os
import stat
import re
import sys
import shutil
import gzip
import socket
import time
import errno
import codecs
from . import Globals, Time, log, user_group, C

try:
    import win32file, winnt
except ImportError:
    pass


class SkipFileException(Exception):
    """Signal that the current file should be skipped but then continue

	This exception will often be raised when there is problem reading
	an individual file, but it makes sense for the rest of the backup
	to keep going.

	"""
    pass


class RPathException(Exception):
    pass


def copyfileobj(inputfp, outputfp):


def cmpfileobj(fp1, fp2):


def check_for_files(*rps):
    """Make sure that all the rps exist, raise error if not"""
    for rp in rps:
        if not rp.lstat():
            raise RPathException(
                "File %s does not exist" % rp.get_safeindexpath())


def move(rpin, rpout):
    """Move rpin to rpout, renaming if possible"""
    try:
        rename(rpin, rpout)
    except os.error:
        copy(rpin, rpout)
        rpin.delete()


def copy(rpin, rpout, compress=0):
    """Copy RPath rpin to rpout.  Works for symlinks, dirs, etc.

	Returns close value of input for regular file, which can be used
	to pass hashes on.

	"""


def cmp(rpin, rpout):
    """True if rpin has the same data as rpout

	cmp does not compare file ownership, permissions, or times, or
	examine the contents of a directory.

	"""


def copy_attribs(rpin, rpout):
    """Change file attributes of rpout to match rpin

	Only changes the chmoddable bits, uid/gid ownership, and
	timestamps, so both must already exist.

	"""


def copy_attribs_inc(rpin, rpout):
    """Change file attributes of rpout to match rpin

	Like above, but used to give increments the same attributes as the
	originals.  Therefore, don't copy all directory acl and
	permissions.

	"""


def cmp_attribs(rp1, rp2):
    """True if rp1 has the same file attributes as rp2

	Does not compare file access times.  If not changing
	ownership, do not check user/group id.

	"""


def rename(rp_source, rp_dest):


def make_file_dict(filename):
    """Generate the data dictionary for the given RPath

	This is a global function so that os.name can be called locally,
	thus avoiding network lag and so that we only need to send the
	filename over the network, thus avoiding the need to pickle an
	(incomplete) rpath object.
	"""



def make_socket_local(rpath):
    """Make a local socket at the given path

	This takes an rpath so that it will be checked by Security.
	(Miscellaneous strings will not be.)

	"""
    assert rpath.conn is Globals.local_connection
    rpath.conn.os.mknod(rpath.path, stat.S_IFSOCK)


def gzip_open_local_read(rpath):
    """Return open GzipFile.  See security note directly above"""
    assert rpath.conn is Globals.local_connection
    return GzipFile(rpath.path, "rb")


def open_local_read(rpath):
    """Return open file (provided for security reasons)"""
    assert rpath.conn is Globals.local_connection
    return open(rpath.path, "rb")


def get_incfile_info(basename):
    """Returns None or tuple of
	(is_compressed, timestr, type, and basename)"""


def delete_dir_no_files(rp):
    """Deletes the directory at rp.path if empty. Raises if the
	directory contains files."""
    assert rp.isdir()
    if rp.contains_files():
        raise RPathException("Directory contains files.")
    rp.delete()


class RORPath:
    """Read Only RPath - carry information about a path

	These contain information about a file, and possible the file's
	data, but do not have a connection and cannot be written to or
	changed.  The advantage of these objects is that they can be
	communicated by encoding their index and data dictionary.

	"""

    def __init__(self, index, data=None):
        self.index = tuple(map(os.fsencode, index))
        if data: self.data = data
        else: self.data = {'type': None}  # signify empty file
        self.file = None

    def zero(self):
        """Set inside of self to type None"""
        self.data = {'type': None}
        self.file = None

    def make_zero_dir(self, dir_rp):
        """Set self.data the same as dir_rp.data but with safe permissions"""
        self.data = dir_rp.data.copy()
        self.data['perms'] = 0o700

    def __eq__(self, other):
        """True iff the two rorpaths are equivalent"""
        if self.index != other.index: return None

        for key in list(self.data.keys()):  # compare dicts key by key
            if self.issym() and key in ('uid', 'gid', 'uname', 'gname'):
                pass  # Don't compare gid/uid for symlinks
            elif key == 'atime' and not Globals.preserve_atime:
                pass
            elif key == 'ctime':
                pass
            elif key == 'nlink':
                pass
            elif key == 'size' and not self.isreg():
                pass
            elif key == 'ea' and not Globals.eas_active:
                pass
            elif key == 'acl' and not Globals.acls_active:
                pass
            elif key == 'win_acl' and not Globals.win_acls_active:
                pass
            elif key == 'carbonfile' and not Globals.carbonfile_active:
                pass
            elif key == 'resourcefork' and not Globals.resource_forks_active:
                pass
            elif key == 'uname' or key == 'gname':
                # here for legacy reasons - 0.12.x didn't store u/gnames
                other_name = other.data.get(key, None)
                if (other_name and other_name != "None"
                        and other_name != self.data[key]):
                    return None
            elif ((key == 'inode' or key == 'devloc')
                  and (not self.isreg() or self.getnumlinks() == 1
                       or not Globals.compare_inode
                       or not Globals.preserve_hardlinks)):
                pass
            else:
                try:
                    other_val = other.data[key]
                except KeyError:
                    return None
                if self.data[key] != other_val: return None
        return 1

    def equal_loose(self, other):
        """True iff the two rorpaths are kinda equivalent

		Sometimes because permissions cannot be set, a file cannot be
		replicated exactly on the remote side.  This function tells
		you whether the two files are close enough.  self must be the
		original rpath.

		"""


		This is necessary in case the RORPath is carrying around a
		file object, which can't/shouldn't be pickled.

		"""
        return (self.index, self.data)

    def __setstate__(self, rorp_state):
        """Reproduce RORPath from __getstate__ output"""
        self.index, self.data = rorp_state

    def getRORPath(self):
        """Return new rorpath based on self"""
        return RORPath(self.index, self.data.copy())

    def lstat(self):
        """Returns type of file

		The allowable types are None if the file doesn't exist, 'reg'
		for a regular file, 'dir' for a directory, 'dev' for a device
		file, 'fifo' for a fifo, 'sock' for a socket, and 'sym' for a
		symlink.
		
		"""


		For instance, if the index is (b"a", b"b"), return ("a", "b")

		"""
        return tuple(map(lambda f: f.decode(errors='replace'), self.index))

    def get_indexpath(self):
        """Return path of index portion

		For instance, if the index is ("a", "b"), return "a/b".

		"""


    def get_safeindexpath(self):
        """Return safe path of index even with names throwing UnicodeEncodeError

		For instance, if the index is ("a", "b"), return "'a/b'".

		"""
        return self.get_indexpath().decode(errors='replace')

    def get_attached_filetype(self):
        """If there is a file attached, say what it is

		Currently the choices are 'snapshot' meaning an exact copy of
		something, and 'diff' for an rdiff style diff.

		"""




		This indicates that a file's data need not be transferred
		because it is hardlinked on the remote side.

		"""


		Instead of writing to the traditional mirror file, store
		mirror information in filename in the long filename
		directory.

		"""
        self.data['mirrorname'] = filename

    def has_alt_inc_name(self):
        """True if rorp has an alternate increment base specified"""
        return 'incname' in self.data

    def get_alt_inc_name(self):
        """Return alternate increment base (used for long name support)"""
        return self.data['incname']

    def set_alt_inc_name(self, name):
        """Set alternate increment name to name

		If set, increments will be in the long name directory with
		name as their base.  If the alt mirror name is set, this
		should be set to the same.

		"""
        self.data['incname'] = name

    def has_sha1(self):
        """True iff self has its sha1 digest set"""
        return 'sha1' in self.data

    def get_sha1(self):
        """Return sha1 digest.  Causes exception unless set_sha1 first"""
        return self.data['sha1']

    def set_sha1(self, digest):
        """Set sha1 hash (should be in hexdecimal)"""
        self.data['sha1'] = digest


class RPath(RORPath):
    """Remote Path class - wrapper around a possibly non-local pathname

	This class contains a dictionary called "data" which should
	contain all the information about the file sufficient for
	identification (i.e. if two files have the the same (==) data
	dictionary, they are the same file).

	"""
    regex_chars_to_quote = re.compile(b"[\\\\\\\"\\$`]")

    def __init__(self, connection, base, index=(), data=None):
        """RPath constructor

		connection = self.conn is the Connection the RPath will use to
		make system calls, and index is the name of the rpath used for
		comparison, and should be a tuple consisting of the parts of
		the rpath after the base split up.  For instance ("foo",
		"bar") for "foo/bar" (no base), and ("local", "bin") for
		"/usr/local/bin" if the base is "/usr".

		For the root directory "/", the index is empty and the base is
		"/".

		"""


		The rpath's connection will be encoded as its conn_number.  It
		and the other information is put in a tuple. Data and any attached
		file won't be saved.

		"""
        return (self.conn.conn_number, self.base, self.index, self.data)

    def __setstate__(self, rpath_state):
        """Reproduce RPath from __getstate__ output"""
        conn_number, self.base, self.index, self.data = rpath_state
        self.conn = Globals.connection_dict[conn_number]
        self.path = os.path.join(self.base, *self.index)



    def check_consistency(self):
        """Raise an error if consistency of rp broken

		This is useful for debugging when the cache and disk get out
		of sync and you need to find out where it happened.

		"""


		This just means that redundant /'s will be removed, including
		the trailing one, even for directories.  ".." components will
		be retained.

		"""


    def dirsplit(self):
        """Returns a tuple of strings (dirname, basename)

		Basename is never '' unless self is root, so it is unlike
		os.path.basename.  If path is just above root (so dirname is
		root), then dirname is ''.  In all other cases dirname is not
		the empty string.  Also, dirsplit depends on the format of
		self, so basename could be ".." and dirname could be a
		subdirectory.  For an atomic relative path, dirname will be
		'.'.

		"""


    def get_path(self):
        """Just a getter for the path variable that can be overwritten by QuotedRPath"""
        return self.path

    def get_safepath(self, somepath=None):
        """Return safely decoded version of path into the current encoding

		it's meant only for logging and outputting to user

		"""


		If compress is true, data written/read will be gzip
		compressed/decompressed on the fly.  The extra complications
		below are for security reasons - try to make the extent of the
		risk apparent from the remote call.

		"""


		If compress is true, fp will be gzip compressed before being
		written to self.  Returns closing value of fp.

		"""


		Also sets various inc information used by the *inc* functions.

		"""


		If fp is none, get the file description by opening the file.
		This can be useful for directories.

		"""


    def fsync_local(self, thunk=None):
        """fsync current file, run locally

		If thunk is given, run it before syncing but after gathering
		the file's file descriptor.

		"""


		If map_names is true, map the ids in acl by user/group names.

		"""


class RPathFileHook:
    """Look like a file, but add closing hook"""

    def __init__(self, file, closing_thunk):
        self.file = file
        self.closing_thunk = closing_thunk

    def read(self, length=-1):
        return self.file.read(length)

    def write(self, buf):
        return self.file.write(buf)

    def close(self):
        """Close file and then run closing thunk"""
        result = self.file.close()
        self.closing_thunk()
        return result


class GzipFile(gzip.GzipFile):
    """Like gzip.GzipFile, except remove destructor

	The default GzipFile's destructor prints out some messy error
	messages.  Use this class instead to clean those up.

	"""

    def __init__(self, filename=None, mode=None):
        """ This is needed because we need to write an
		encoded filename to the file, but use normal
		unicode with the filename."""
        if mode and 'b' not in mode:
            mode += 'b'
        fileobj = open(filename, mode or 'rb')
        gzip.GzipFile.__init__(self, filename, mode=mode, fileobj=fileobj)

    def __del__(self):
        pass




class MaybeGzip:
    """Represent a file object that may or may not be compressed

	We don't want to compress 0 length files.  This class lets us
	delay the opening of the file until either the first write (so we
	know it has data and should be compressed), or close (when there's
	no data).

	"""



def setdata_local(rpath):
    """Set eas/acls, uid/gid, resource fork in data dictionary

	This is a global function because it must be called locally, since
	these features may exist or not depending on the connection.

	"""



def carbonfile_get(rpath):
    """Return carbonfile value for local rpath"""
    # Note, after we drop support for Mac OS X 10.0 - 10.3, it will no longer
    # be necessary to read the finderinfo struct since it is a strict subset
    # of the data stored in the com.apple.FinderInfo extended attribute
    # introduced in 10.4. Indeed, FSpGetFInfo() is deprecated on 10.4.
    from Carbon.File import FSSpec
    from Carbon.File import FSRef
    import Carbon.Files
    import MacOS
    try:
        fsobj = FSSpec(rpath.path)
        finderinfo = fsobj.FSpGetFInfo()
        cataloginfo, d1, d2, d3 = FSRef(fsobj).FSGetCatalogInfo(
            Carbon.Files.kFSCatInfoCreateDate)
        cfile = {
            'creator': finderinfo.Creator,
            'type': finderinfo.Type,
            'location': finderinfo.Location,
            'flags': finderinfo.Flags,
            'createDate': cataloginfo.createDate[1]
        }
        return cfile
    except MacOS.Error:
        log.Log("Cannot read carbonfile information from %s" % (rpath.path, ),
                2)
        return None


# These functions are overwritten by the eas_acls.py module.  We can't
# import that module directly because of circular dependency problems.
def acl_get(rp):
    assert 0


def get_blank_acl(index):
    assert 0


def ea_get(rp):
    assert 0


def get_blank_ea(index):
    assert 0


def win_acl_get(rp):
    assert 0


def write_win_acl(rp):
    assert 0


def get_blank_win_acl():
    assert 0
