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
"""Coordinate corresponding files with different names

For instance, some source filenames may contain characters not allowed
on the mirror end.  These files must be called something different on
the mirror end, so we escape the offending characters with semicolons.

One problem/complication is that all this escaping may put files over
the 256 or whatever limit on the length of file names.  (We just don't
handle that error.)

"""


from . import Globals, log, rpath

# If true, enable character quoting, and set characters making
# regex-style range.
chars_to_quote = None

# These compiled regular expressions are used in quoting and unquoting
chars_to_quote_regexp = None
unquoting_regexp = None

# Use given char to quote.  Default is set in Globals.
quoting_char = None


class QuotingException(Exception):
    pass


def set_init_quote_vals():
    """Set quoting value from Globals on all conns"""
    for conn in Globals.connections:
        conn.FilenameMapping.set_init_quote_vals_local()


def set_init_quote_vals_local():
    """Set value on local connection, initialize regexps"""
    global chars_to_quote, quoting_char
    chars_to_quote = Globals.chars_to_quote
    if len(Globals.quoting_char) != 1:
        log.Log.FatalError("Expected single character for quoting char,"
                           "got '%a' instead" % (Globals.quoting_char, ))
    quoting_char = Globals.quoting_char
    init_quoting_regexps()


def init_quoting_regexps():
    """Compile quoting regular expressions"""
    global chars_to_quote_regexp, unquoting_regexp
    assert chars_to_quote and isinstance(chars_to_quote, bytes), \
        "Chars to quote are wrong: %a" % chars_to_quote
    try:
        chars_to_quote_regexp = \
           re.compile(b"[%b]|%b" % (chars_to_quote, quoting_char), re.S)
        unquoting_regexp = re.compile(b"%b[0-9]{3}" % quoting_char, re.S)
    except re.error:
        log.Log.FatalError("Error '%s' when processing char quote list %r" %
                           (re.error, chars_to_quote))


def quote(path):
    """Return quoted version of given path

	Any characters quoted will be replaced by the quoting char and
	the ascii number of the character.  For instance, "10:11:12"
	would go to "10;05811;05812" if ":" were quoted and ";" were
	the quoting character.

	"""
    QuotedPath = chars_to_quote_regexp.sub(quote_single, path)
    if not Globals.escape_dos_devices and not Globals.escape_trailing_spaces:
        return QuotedPath

    # Escape a trailing space or period (invalid in names on FAT32 under DOS,
    # Windows and modern Linux)
    if Globals.escape_trailing_spaces:
        if len(QuotedPath) and (QuotedPath[-1] == ord(' ')
                                or QuotedPath[-1] == ord('.')):
            QuotedPath = QuotedPath[:-1] + \
             b"%b%03d" % (quoting_char, QuotedPath[-1])

        if not Globals.escape_dos_devices:
            return QuotedPath

    # Escape first char of any special DOS device files even if filename has an
    # extension.  Special names are: aux, prn, con, nul, com0-9, and lpt1-9.
    if not re.search(br"^aux(\..*)*$|^prn(\..*)*$|^con(\..*)*$|^nul(\..*)*$|" \
         br"^com[0-9](\..*)*$|^lpt[1-9]{1}(\..*)*$", QuotedPath, \
         re.I):
        return QuotedPath
    return b"%b%03d" % (quoting_char, QuotedPath[0]) + QuotedPath[1:]


def quote_single(match):
    """Return replacement for a single character"""
    return b"%b%03d" % (quoting_char, ord(match.group()))


def unquote(path):
    """Return original version of quoted filename"""
    return unquoting_regexp.sub(unquote_single, path)


def unquote_single(match):
    """Unquote a single quoted character"""
    if not len(match.group()) == 4:
        raise QuotingException("Quoted group wrong size: %a" % match.group())
    try:
        return os.fsencode(chr(int(match.group()[1:])))
    except ValueError:
        raise QuotingException("Quoted out of range: %a" % match.group())


class QuotedRPath(rpath.RPath):
    """RPath where the filename is quoted version of index

	We use QuotedRPaths so we don't need to remember to quote RPaths
	derived from this one (via append or new_index).  Note that only
	the index is quoted, not the base.

	"""

    def __init__(self, connection, base, index=(), data=None):
        """Make new QuotedRPath"""
        super().__init__(connection, base, index, data)
        self.quoted_index = tuple(map(quote, self.index))
        # we need to recalculate path and data on the basis of
        # quoted_index (parent class does it on the basis of index)
        if base is not None:
            self.path = os.path.join(self.base, *self.quoted_index)
            if data is None: self.setdata()

    def __setstate__(self, rpath_state):
        """Reproduce QuotedRPath from __getstate__ output"""
        conn_number, self.base, self.index, self.data = rpath_state
        self.conn = Globals.connection_dict[conn_number]
        self.quoted_index = tuple(map(quote, self.index))
        self.path = os.path.join(self.base, *self.quoted_index)

    def listdir(self):
        """Return list of unquoted filenames in current directory

		We want them unquoted so that the results can be sorted
		correctly and append()ed to the currect QuotedRPath.

		"""


def get_quoted_sep_base(filename):
    """Get QuotedRPath from filename assuming last bit is quoted"""
    return get_quotedrpath(rpath.RPath(Globals.local_connection, filename), 1)


def update_quoting(rbdir):
    """Update the quoting of a repository by renaming any
	files that should be quoted differently.
	"""

    def requote(name):
        unquoted_name = unquote(name)
        quoted_name = quote(unquoted_name)
        if name != quoted_name:
            return quoted_name
        else:
            return None

    def process(dirpath_rp, name, list):
        new_name = requote(name)
        if new_name:
            if list:
                list.remove(name)
                list.append(new_name)
            name_rp = dirpath_rp.append(name)
            new_rp = dirpath_rp.append(new_name)
            log.Log(
                "Re-quoting %s to %s" % (name_rp.get_safepath(),
                                         new_rp.get_safepath()), 5)
            rpath.move(name_rp, new_rp)

    assert rbdir.conn is Globals.local_connection
    mirror_rp = rbdir.get_parent_rp()
    mirror = mirror_rp.path

    log.Log("Re-quoting repository %s" % mirror_rp.get_safepath(), 3)

    try:
        os_walk = os.walk
    except AttributeError:
        os_walk = walk

    for dirpath, dirs, files in os_walk(mirror):
        dirpath_rp = mirror_rp.newpath(dirpath)

        for name in dirs:
            process(dirpath_rp, name, dirs)
        for name in files:
            process(dirpath_rp, name, None)


"""
os.walk() copied directly from Python 2.5.1's os.py

Backported here for Python 2.2 support. os.walk() was first added
in Python 2.3.
"""


def walk(top, topdown=True, onerror=None):
    from os import error, listdir
    from os.path import join, isdir, islink
    # We may not have read permission for top, in which case we can't
    # get a list of the files the directory contains.  os.path.walk
    # always suppressed the exception then, rather than blow up for a
    # minor reason when (say) a thousand readable directories are still
    # left to visit.  That logic is copied here.
    try:
        # Note that listdir and error are globals in this module due
        # to earlier import-*.
        names = listdir(top)
    except error as err:
        if onerror is not None:
            onerror(err)
        return

    dirs, nondirs = [], []
    for name in names:
        if isdir(join(top, name)):
            dirs.append(name)
        else:
            nondirs.append(name)

    if topdown:
        yield top, dirs, nondirs
    for name in dirs:
        path = join(top, name)
        if not islink(path):
            for x in walk(path, topdown, onerror):
                yield x
    if not topdown:
        yield top, dirs, nondirs
