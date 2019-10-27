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
"""Convert an iterator to a file object and vice-versa"""

import pickle
import array
import types
from . import Globals, C, robust, log, rpath


class IterFileException(Exception):
    pass


class UnwrapFile:
    """Contains some basic methods for parsing a file containing an iter"""

    def __init__(self, file):
        self.file = file

    def _get(self):
        """Return pair (type, data) next in line on the file

		type is a single character which is either
		"o" for an object,
		"f" for file,
		"c" for a continution of a file,
		"h" for the close value of a file
		"e" for an exception, or
		None if no more data can be read.

		Data is either the file's data, if type is "c" or "f", or the
		actual object if the type is "o", "e", or "r"

		"""



class IterWrappingFile(UnwrapFile):
    """An iterator generated from a file.

	Initialize with a file type object, and then it will return the
	elements of the file in order.

	"""

    def __init__(self, file):
        UnwrapFile.__init__(self, file)
        self.currently_in_file = None

    def __iter__(self):
        return self




class IterVirtualFile(UnwrapFile):
    """Another version of a pretend file

	This is returned by IterWrappingFile when a file is embedded in
	the main file that the IterWrappingFile is based around.

	"""

    def __init__(self, iwf, initial_data):
        """Initializer

		initial_data is the data from the first block of the file.
		iwf is the iter wrapping file that spawned this
		IterVirtualFile.

		"""



class FileWrappingIter:
    """A file interface wrapping around an iterator

	This is initialized with an iterator, and then converts it into a
	stream of characters.  The object will evaluate as little of the
	iterator as is necessary to provide the requested bytes.

	The actual file is a sequence of marshaled objects, each preceded
	by 8 bytes which identifies the following the type of object, and
	specifies its length.  File objects are not marshalled, but the
	data is written in chunks of Globals.blocksize, and the following
	blocks can identify themselves as continuations.

	"""


		Returns None if we have reached the end of the iterator,
		otherwise return true.

		"""
        if self.currently_in_file: self.addfromfile(b"c")
        else:
            try:
                currentobj = next(self.iter)
            except StopIteration:
                return None
            if hasattr(currentobj, "read") and hasattr(currentobj, "close"):
                self.currently_in_file = currentobj
                self.addfromfile(b"f")
            else:
                pickled_data = pickle.dumps(currentobj, 1)
                self.array_buf.frombytes(b"o")
                self.array_buf.frombytes(self._i2b(len(pickled_data), 7))
                self.array_buf.frombytes(pickled_data)
        return 1

    def addfromfile(self, prefix_letter):
        """Read a chunk from the current file and add to array_buf

		prefix_letter and the length will be prepended to the file
		data.  If there is an exception while reading the file, the
		exception will be added to array_buf instead.

		"""
        buf = robust.check_common_error(self.read_error_handler,
                                        self.currently_in_file.read,
                                        [Globals.blocksize])
        if buf is None:  # error occurred above, encode exception
            self.currently_in_file = None
            excstr = pickle.dumps(self.last_exception, 1)
            total = b"".join((b'e', self._i2b(len(excstr), 7), excstr))
        else:
            total = b"".join((prefix_letter, self._i2b(len(buf), 7), buf))
            if buf == b"":  # end of file
                cstr = pickle.dumps(self.currently_in_file.close(), 1)
                self.currently_in_file = None
                total += b"".join((b'h', self._i2b(len(cstr), 7), cstr))
        self.array_buf.frombytes(total)

    def read_error_handler(self, exc, blocksize):
        """Log error when reading from file"""
        self.last_exception = exc
        return None

    def _i2b(self, i, size=0):
        """Convert int to string using big endian byteorder"""
        if (size == 0):
            size = (i.bit_length() + 7) // 8
        return i.to_bytes(size, byteorder='big')

    def close(self):
        self.closed = 1


class MiscIterFlush:
    """Used to signal that a MiscIterToFile should flush buffer"""
    pass


class MiscIterFlushRepeat(MiscIterFlush):
    """Flush, but then cause Misc Iter to yield this same object

	Thus if we put together a pipeline of these, one MiscIterFlushRepeat
	can cause all the segments to flush in sequence.

	"""
    pass


class MiscIterToFile(FileWrappingIter):
    """Take an iter and give it a file-ish interface

	This expands on the FileWrappingIter by understanding how to
	process RORPaths with file objects attached.  It adds a new
	character "r" to mark these.

	This is how we send signatures and diffs across the line.  As
	sending each one separately via a read() call would result in a
	lot of latency, the read()'s are buffered - a read() call with no
	arguments will return a variable length string (possibly empty).

	To flush the MiscIterToFile, have the iterator yield a
	MiscIterFlush class.

	"""

    def __init__(self, rpiter, max_buffer_bytes=None, max_buffer_rps=None):
        """MiscIterToFile initializer

		max_buffer_bytes is the maximum size of the buffer in bytes.
		max_buffer_rps is the maximum size of the buffer in rorps.

		"""



class FileToMiscIter(IterWrappingFile):


		This is like UnwrapFile._get() but reads in variable length
		blocks.  Also type "z" is allowed, which means end of
		iterator.  An empty read() is not considered to mark the end
		of remote iter.

		"""



class ErrorFile:
    """File-like that just raises error (used by FileToMiscIter above)"""

    def __init__(self, exc):
        """Initialize new ErrorFile.  exc is the exception to raise on read"""
        self.exc = exc

    def read(self, l=-1):
        raise self.exc

    def close(self):
        return None


from . import iterfile
