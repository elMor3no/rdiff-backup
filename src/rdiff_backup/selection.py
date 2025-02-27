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
"""Iterate exactly the requested files in a directory

Parses includes and excludes to yield correct files.  More
documentation on what this code does can be found on the man page.

"""


from . import FilenameMapping, robust, rpath, Globals, log, rorpiter


class SelectError(Exception):
    """Some error dealing with the Select class"""
    pass


class FilePrefixError(SelectError):
    """Signals that a specified file doesn't start with correct prefix"""
    pass


class GlobbingError(SelectError):
    """Something has gone wrong when parsing a glob string"""
    pass


class Select:
    """Iterate appropriate RPaths in given directory

	This class acts as an iterator on account of its next() method.
	Basically, it just goes through all the files in a directory in
	order (depth-first) and subjects each file to a bunch of tests
	(selection functions) in order.  The first test that includes or
	excludes the file means that the file gets included (iterated) or
	excluded.  The default is include, so with no tests we would just
	iterate all the files in the directory in order.

	The one complication to this is that sometimes we don't know
	whether or not to include a directory until we examine its
	contents.  For instance, if we want to include all the **.py
	files.  If /home/ben/foo.py exists, we should also include /home
	and /home/ben, but if these directories contain no **.py files,
	they shouldn't be included.  For this reason, a test may not
	include or exclude a directory, but merely "scan" it.  If later a
	file in the directory gets included, so does the directory.

	As mentioned above, each test takes the form of a selection
	function.  The selection function takes an rpath, and returns:

	None - means the test has nothing to say about the related file
	0 - the file is excluded by the test
	1 - the file is included
	2 - the test says the file (must be directory) should be scanned

	Also, a selection function f has a variable f.exclude which should
	be true iff f could potentially exclude some file.  This is used
	to signal an error if the last function only includes, which would
	be redundant and presumably isn't what the user intends.

	"""
    # This re should not match normal filenames, but usually just globs
    glob_re = re.compile(b"(.*[*?[\\\\]|ignorecase\\:)", re.I | re.S)

    def __init__(self, rootrp):
        """Select initializer.  rpath is the root directory"""
        assert isinstance(rootrp, rpath.RPath)
        self.selection_functions = []
        self.rpath = rootrp
        self.prefix = self.rpath.path

    def set_iter(self, sel_func=None):
        """Initialize more variables, get ready to iterate

		Selection function sel_func is called on each rpath and is
		usually self.Select.  Returns self just for convenience.

		"""


        def error_handler(exc, filename):
            log.ErrorLog.write_if_open("ListError", rpath.index + (filename, ),
                                       exc)
            return None

        def diryield(rpath):
            """Generate relevant files in directory rpath

			Returns (rpath, num) where num == 0 means rpath should be
			generated normally, num == 1 means the rpath is a directory
			and should be included iff something inside is included.

			"""


		rec_func is usually the same as this function and is what
		Iterate uses to find files in subdirectories.  It is used in
		iterate_starting_from.

		sel_func is the selection function to use on the rpaths.  It
		is usually self.Select.

		"""


		The tuples have the form (option string, additional argument)
		and are created when the initial commandline arguments are
		read.  The reason for the extra level of processing is that
		the filelists may only be openable by the main connection, but
		the selection functions need to be on the backup reader or
		writer side.  When the initial arguments are parsed the right
		information is sent over the link.

		"""
        filelists_index = 0
        try:
            for opt, arg in argtuples:
                if opt == "--exclude":
                    self.add_selection_func(self.glob_get_sf(arg, 0))
                elif opt == "--exclude-if-present":
                    self.add_selection_func(self.presence_get_sf(arg, 0))
                elif opt == "--exclude-device-files":
                    self.add_selection_func(self.devfiles_get_sf(0))
                elif opt == "--exclude-symbolic-links":
                    self.add_selection_func(self.symlinks_get_sf(0))
                elif opt == "--exclude-sockets":
                    self.add_selection_func(self.sockets_get_sf(0))
                elif opt == "--exclude-fifos":
                    self.add_selection_func(self.fifos_get_sf(0))
                elif opt == "--exclude-filelist":
                    self.add_selection_func(
                        self.filelist_get_sf(filelists[filelists_index], 0,
                                             arg))
                    filelists_index += 1
                elif opt == "--exclude-globbing-filelist":
                    list(
                        map(
                            self.add_selection_func,
                            self.filelist_globbing_get_sfs(
                                filelists[filelists_index], 0, arg)))
                    filelists_index += 1
                elif opt == "--exclude-other-filesystems":
                    self.add_selection_func(self.other_filesystems_get_sf(0))
                elif opt == "--exclude-regexp":
                    self.add_selection_func(self.regexp_get_sf(arg, 0))
                elif opt == "--exclude-special-files":
                    self.add_selection_func(self.special_get_sf(0))
                elif opt == "--include":
                    self.add_selection_func(self.glob_get_sf(arg, 1))
                elif opt == "--include-filelist":
                    self.add_selection_func(
                        self.filelist_get_sf(filelists[filelists_index], 1,
                                             arg))
                    filelists_index += 1
                elif opt == "--include-globbing-filelist":
                    list(
                        map(
                            self.add_selection_func,
                            self.filelist_globbing_get_sfs(
                                filelists[filelists_index], 1, arg)))
                    filelists_index += 1
                elif opt == "--include-regexp":
                    self.add_selection_func(self.regexp_get_sf(arg, 1))
                elif opt == "--include-special-files":
                    self.add_selection_func(self.special_get_sf(1))
                elif opt == "--include-symbolic-links":
                    self.add_selection_func(self.symlinks_get_sf(1))
                elif opt == "--max-file-size":
                    self.add_selection_func(self.size_get_sf(1, arg))
                elif opt == "--min-file-size":
                    self.add_selection_func(self.size_get_sf(0, arg))
                else:
                    assert 0, "Bad selection option %s" % opt
        except SelectError as e:
            self.parse_catch_error(e)
        assert filelists_index == len(filelists)

        self.parse_last_excludes()
        self.parse_rbdir_exclude()

    def parse_catch_error(self, exc):
        """Deal with selection error exc"""
        if isinstance(exc, FilePrefixError):
            log.Log.FatalError("""Fatal Error: The file specification
    '%s'
cannot match any files in the base directory
    '%s'
Useful file specifications begin with the base directory or some
pattern (such as '**') which matches the base directory.""" % (exc,
                                                               self.prefix))
        elif isinstance(exc, GlobbingError):
            log.Log.FatalError("Fatal Error while processing expression\n"
                               "%s" % exc)
        else:
            raise

    def parse_rbdir_exclude(self):
        """Add exclusion of rdiff-backup-data dir to front of list"""
        self.add_selection_func(
            self.glob_get_tuple_sf((b"rdiff-backup-data", ), 0), 1)

    def parse_last_excludes(self):
        """Exit with error if last selection function isn't an exclude"""
        if (self.selection_functions
                and not self.selection_functions[-1].exclude):
            log.Log.FatalError("""Last selection expression:
    %s
only specifies that files be included.  Because the default is to
include all files, the expression is redundant.  Exiting because this
probably isn't what you meant.""" % (self.selection_functions[-1].name, ))



    def filelist_get_sf(self, filelist_fp, inc_default, filelist_name):
        """Return selection function by reading list of files

		The format of the filelist is documented in the man page.
		filelist_fp should be an (open) file object.
		inc_default should be true if this is an include list,
		false for an exclude list.
		filelist_name is just a string used for logging.

		"""


		pair will be of form (index, include), where index is another
		tuple, and include is 1 if the line specifies that we are
		including a file.  The default is given as an argument.
		prefix is the string that the index is relative to.

		"""


		Returns a pair (include, move_on).  include is None if the
		tuple doesn't match either way, and 0/1 if the tuple excludes
		or includes the rpath.

		move_on is true if the tuple cannot match a later index, and
		so we should move on to the next tuple in the index.

		"""


		filelist_fp should be an open file object
		inc_default is true iff this is an include list
		list_name is just the name of the list, used for logging
		See the man page on --[include/exclude]-globbing-filelist

		"""

		
		RPath is matched if pred returns true on it.  Name is a string
		summarizing the test to the user.

		"""


		Some of the parsing is better explained in
		filelist_parse_line.  The reason this is split from normal
		globbing is things are a lot less complicated if no special
		globbing characters are used.

		"""


		The basic idea is to turn glob_str into a regular expression,
		and just use the normal regular expression.  There is a
		complication because the selection function should return '2'
		(scan) for directories which may contain a file which matches
		the glob_str.  So we break up the glob string into parts, and
		any file which matches an initial sequence of glob parts gets
		scanned.

		Thanks to Donovan Baarda who provided some code which did some
		things similar to this.

		"""


		Currently only the ?, *, [], and ** expressions are supported.
		Ranges like [a-z] are also currently unsupported.  These special
		characters can be quoted by prepending them with a backslash.

		This function taken with minor modifications from efnmatch.py
		by Donovan Baarda.

		"""



class FilterIter:
    """Filter rorp_iter using a Select object, removing excluded rorps"""

    def __init__(self, select, rorp_iter):
        """Constructor

		Input is the Select object to use and the iter of rorps to be
		filtered.  The rorps will be converted to rps using the Select
		base.

		"""


class FilterIterITRB(rorpiter.ITRBranch):
    """ITRBranch used in above FilterIter class

	The reason this is necessary is because for directories sometimes
	we don't know whether a rorp is excluded until we see what is in
	the directory.

	"""

    def __init__(self, select, rorp_cache):
        """Initialize FilterIterITRB.  Called by IterTreeReducer.

		select should be the relevant Select object used to test the
		rps.  rorp_cache is the list rps should be appended to if they
		aren't excluded.

		"""

