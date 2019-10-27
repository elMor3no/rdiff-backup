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
"""Store and retrieve metadata in destination directory

The plan is to store metadata information for all files in the
destination directory in a special metadata file.  There are two
reasons for this:

1)  The filesystem of the mirror directory may not be able to handle
    types of metadata that the source filesystem can.  For instance,
    rdiff-backup may not have root access on the destination side, so
    cannot set uid/gid.  Or the source side may have ACLs and the
    destination side doesn't.

	Hopefully every file system can store binary data.  Storing
	metadata separately allows us to back up anything (ok, maybe
	strange filenames are still a problem).

2)  Metadata can be more quickly read from a file than it can by
    traversing the mirror directory over and over again.  In many
    cases most of rdiff-backup's time is spent compaing metadata (like
    file size and modtime), trying to find differences.  Reading this
    data sequentially from a file is significantly less taxing than
    listing directories and statting files all over the mirror
    directory.

The metadata is stored in a text file, which is a bunch of records
concatenated together.  Each record has the format:

File <filename>
  <field_name1> <value>
  <field_name2> <value>
  ...

Where the lines are separated by newlines.  See the code below for the
field names and values.

"""


from . import log, Globals, rpath, Time, robust, increment, rorpiter


class ParsingError(Exception):
    """This is raised when bad or unparsable data is received"""
    pass


def carbonfile2string(cfile):


def string2carbonfile(data):
    """Re-constitute CarbonFile data from a string stored by 
	carbonfile2string."""
    retval = {}
    for component in data.split('|'):
        key, value = component.split(':')
        if key == 'creator':
            retval['creator'] = binascii.unhexlify(value)
        elif key == 'type':
            retval['type'] = binascii.unhexlify(value)
        elif key == 'location':
            a, b = value.split(',')
            retval['location'] = (int(a), int(b))
        elif key == 'flags':
            retval['flags'] = int(value)
        elif key == 'createDate':
            retval['createDate'] = int(value)
    return retval


def RORP2Record(rorpath):


line_parsing_regexp = re.compile(b"^ *([A-Za-z0-9]+) (.+)$", re.M)


def Record2RORP(record_string):
    """Given record_string, return RORPath

	For speed reasons, write the RORPath data dictionary directly
	instead of calling rorpath functions.  Profiling has shown this to
	be a time critical function.

	"""


chars_to_quote = re.compile(b"\\n|\\\\")


def quote_path(path_string):
    """Return quoted version of path_string

	Because newlines are used to separate fields in a record, they are
	replaced with \n.  Backslashes become \\ and everything else is
	left the way it is.

	"""


def unquote_path(quoted_string):


def quoted_filename_to_index(quoted_filename):


class FlatExtractor:


		Here we make sure that the buffer always ends in a newline, so
		we will not be splitting lines in half.

		"""


		The filename is the first group matched by
		regexp_boundary_regexp.

		"""
        assert 0  # subclass


class RorpExtractor(FlatExtractor):
    """Iterate rorps from metadata file"""
    record_boundary_regexp = re.compile(b"(?:\\n|^)(File (.*?))\\n")
    record_to_object = staticmethod(Record2RORP)
    filename_to_index = staticmethod(quoted_filename_to_index)


class FlatFile:
    """Manage a flat file containing info on various files

	This is used for metadata information, and possibly EAs and ACLs.
	The main read interface is as an iterator.  The storage format is
	a flat, probably compressed file, so random access is not
	recommended.

	Even if the file looks like a text file, it is actually a binary file,
	so that (especially) paths can be stored as bytes, without issue
	with encoding / decoding.
	"""
    rp, fileobj, mode = None, None, None
    _buffering_on = 1  # Buffering may be useful because gzip writes are slow
    _record_buffer, _max_buffer_size = None, 100
    _extractor = FlatExtractor  # Override to class that iterates objects
    _object_to_record = None  # Set to function converting object to record
    _prefix = None  # Set to required prefix

    def __init__(self, rp_base, mode, check_path=1, compress=1, callback=None):
        """Open rp (or rp+'.gz') for reading ('r') or writing ('w')

		If callback is available, it will be called on the rp upon
		closing (because the rp may not be known in advance).

		"""


class MetadataFile(FlatFile):
    """Store/retrieve metadata from mirror_metadata as rorps"""
    _prefix = b"mirror_metadata"
    _extractor = RorpExtractor
    _object_to_record = staticmethod(RORP2Record)


class CombinedWriter:



class Manager:


class PatchDiffMan(Manager):
    """Contains functions for patching and diffing metadata

	To save space, we can record a full list of only the most recent
	metadata, using the normal rdiff-backup reverse increment
	strategy.  Instead of using librsync to compute diffs, though, we
	use our own technique so that the diff files are still
	hand-editable.

	A mirror_metadata diff has the same format as a mirror_metadata
	snapshot.  If the record for an index is missing from the diff, it
	indicates no change from the original.  If it is present it
	replaces the mirror_metadata entry, unless it has Type None, which
	indicates the record should be deleted from the original.

	"""


		The iters should be given as a list/tuple in reverse
		chronological order.  The earliest rorp in each iter will
		supercede all the later ones.

		"""

def SetManager():
    global ManagerObj
    ManagerObj = PatchDiffMan()
    return ManagerObj


from . import eas_acls, win_acls  # put at bottom to avoid python circularity bug
