# Copyright 2002, 2003, 2004, 2005 Ben Escoto
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
"""Read increment files and restore to original"""


from . import rorpiter, FilenameMapping


class RestoreError(Exception):
    pass


def Restore(mirror_rp, inc_rpath, target, restore_to_time):
    """Recursively restore mirror and inc_rpath to target at rest_time"""
    MirrorS = mirror_rp.conn.restore.MirrorStruct
    TargetS = target.conn.restore.TargetStruct

    MirrorS.set_mirror_and_rest_times(restore_to_time)
    MirrorS.initialize_rf_cache(mirror_rp, inc_rpath)
    target_iter = TargetS.get_initial_iter(target)
    diff_iter = MirrorS.get_diffs(target_iter)
    TargetS.patch(target, diff_iter)
    MirrorS.close_rf_cache()


def get_inclist(inc_rpath):


def ListChangedSince(mirror_rp, inc_rp, restore_to_time):
    """List the changed files under mirror_rp since rest time

	Notice the output is an iterator of RORPs.  We do this because we
	want to give the remote connection the data in buffered
	increments, and this is done automatically for rorp iterators.
	Encode the lines in the first element of the rorp's index.

	"""


def ListAtTime(mirror_rp, inc_rp, time):
    """List the files in archive at the given time

	Output is a RORP Iterator with info in index.  See ListChangedSince.

	"""
    assert mirror_rp.conn is Globals.local_connection, "Run locally only"
    MirrorStruct.set_mirror_and_rest_times(time)
    MirrorStruct.initialize_rf_cache(mirror_rp, inc_rp)
    old_iter = MirrorStruct.get_mirror_rorp_iter()
    for rorp in old_iter:
        yield rorp


class MirrorStruct:
    """Hold functions to be run on the mirror side"""
    # If selection command line arguments given, use Select here
    _select = None
    # This will be set to the time of the current mirror
    _mirror_time = None
    # This will be set to the exact time to restore to (not restore_to_time)
    _rest_time = None

    @classmethod
    def set_mirror_and_rest_times(cls, restore_to_time):
        """Set class variabels _mirror_time and _rest_time on mirror conn"""
        MirrorStruct._mirror_time = cls.get_mirror_time()
        MirrorStruct._rest_time = cls.get_rest_time(restore_to_time)

    @classmethod
    def get_mirror_time(cls):
        """Return time (in seconds) of latest mirror"""
        cur_mirror_incs = get_inclist(Globals.rbdir.append(b"current_mirror"))
        if not cur_mirror_incs:
            log.Log.FatalError("Could not get time of current mirror")
        elif len(cur_mirror_incs) > 1:
            log.Log("Warning, two different times for current mirror found", 2)
        return cur_mirror_incs[0].getinctime()

    @classmethod
    def get_rest_time(cls, restore_to_time):
        """Return older time, if restore_to_time is in between two inc times

		There is a slightly tricky reason for doing this: The rest of the
		code just ignores increments that are older than restore_to_time.
		But sometimes we want to consider the very next increment older
		than rest time, because rest_time will be between two increments,
		and what was actually on the mirror side will correspond to the
		older one.

		So if restore_to_time is inbetween two increments, return the
		older one.

		"""


    @classmethod
    def get_increment_times(cls, rp=None):
        """Return list of times of backups, including current mirror

		Take the total list of times from the increments.<time>.dir
		file and the mirror_metadata file.  Sorted ascending.

		"""


		Usually we can use the metadata file, but if this is
		unavailable, we may have to build it from scratch.

		If the cls._select object is set, use it to filter out the
		unwanted files from the metadata_iter.

		"""


		subtract_indicies and add_indicies are necessary because we
		may not be restoring from the root index.

		"""
        if index == (): return rorp_iter

        def get_iter():
            for rorp in rorp_iter:
                assert rorp.index[:len(index)] == index, (rorp.index, index)
                rorp.index = rorp.index[len(index):]
                yield rorp

        return get_iter()

    @classmethod
    def get_diffs(cls, target_iter):
        """Given rorp iter of target files, return diffs

		Here the target_iter doesn't contain any actual data, just
		attribute listings.  Thus any diffs we generate will be
		snapshots.

		"""



class TargetStruct:
    """Hold functions to be run on the target side when restoring"""
    _select = None

    @classmethod
    def set_target_select(cls, target, select_opts, *filelists):
        """Return a selection object iterating the rorpaths in target"""
        cls._select = selection.Select(target)
        cls._select.ParseArgs(select_opts, filelists)

    @classmethod
    def get_initial_iter(cls, target):
        """Return selector previously set with set_initial_iter"""
        if cls._select:
            return cls._select.set_iter()
        else:
            return selection.Select(target).set_iter()

    @classmethod
    def patch(cls, target, diff_iter):
        """Patch target with the diffs from the mirror side

		This function and the associated ITRB is similar to the
		patching code in backup.py, but they have different error
		correction requirements, so it seemed easier to just repeat it
		all in this module.

		"""
        ITR = rorpiter.IterTreeReducer(PatchITRB, [target])
        for diff in rorpiter.FillInIter(diff_iter, target):
            log.Log("Processing changed file %s" % diff.get_safeindexpath(), 5)
            ITR(diff.index, diff)
        ITR.Finish()
        target.setdata()


class CachedRF:
    """Store RestoreFile objects until they are needed

	The code above would like to pretend it has random access to RFs,
	making one for a particular index at will.  However, in general
	this involves listing and filtering a directory, which can get
	expensive.

	Thus, when a CachedRF retrieves an RestoreFile, it creates all the
	RFs of that directory at the same time, and doesn't have to
	recalculate.  It assumes the indicies will be in order, so the
	cache is deleted if a later index is requested.

	"""


		Returns false if no rfs are available, which usually indicates
		an error.

		"""



class RestoreFile:
    """Hold data about a single mirror file and its related increments

	self.relevant_incs will be set to a list of increments that matter
	for restoring a regular file.  If the patches are to mirror_rp, it
	will be the first element in self.relevant.incs

	"""

    def __init__(self, mirror_rp, inc_rp, inc_list):
        self.index = mirror_rp.index
        self.mirror_rp = mirror_rp
        self.inc_rp, self.inc_list = inc_rp, inc_list
        self.set_relevant_incs()

    def relevant_incs_string(self):
        """Return printable string of relevant incs, used for debugging"""
        l = ["---- Relevant incs for %s" % ("/".join(self.index), )]
        l.extend([
            "%s %s %s" % (inc.getinctype(), inc.lstat(), inc.path)
            for inc in self.relevant_incs
        ])
        l.append("--------------------------------")
        return "\n".join(l)

    def set_relevant_incs(self):
        """Set self.relevant_incs to increments that matter for restoring

		relevant_incs is sorted newest first.  If mirror_rp matters,
		it will be (first) in relevant_incs.

		"""


		Also discard increments older than rest_time (rest_time we are
		assuming is the exact time rdiff-backup was run, so no need to
		consider the next oldest increment or any of that)

		"""
        incpairs = []
        for inc in self.inc_list:
            time = inc.getinctime()
            if time >= MirrorStruct._rest_time: incpairs.append((time, inc))
        incpairs.sort()
        return [pair[1] for pair in incpairs]

    def get_attribs(self):
        """Return RORP with restored attributes, but no data

		This should only be necessary if the metadata file is lost for
		some reason.  Otherwise the file provides all data.  The size
		will be wrong here, because the attribs may be taken from
		diff.

		"""
        last_inc = self.relevant_incs[-1]
        if last_inc.getinctype() == b'missing':
            return rpath.RORPath(self.index)

        rorp = last_inc.getRORPath()
        rorp.index = self.index
        if last_inc.getinctype() == b'dir': rorp.data['type'] = 'dir'
        return rorp

    def get_restore_fp(self):
        """Return file object of restored data"""

        def get_fp():
            current_fp = self.get_first_fp()
            for inc_diff in self.relevant_incs[1:]:
                log.Log("Applying patch %s" % (inc_diff.get_safeindexpath(), ),
                        7)
                assert inc_diff.getinctype() == b'diff'
                delta_fp = inc_diff.open("rb", inc_diff.isinccompressed())
                new_fp = tempfile.TemporaryFile()
                Rdiff.write_patched_fp(current_fp, delta_fp, new_fp)
                new_fp.seek(0)
                current_fp = new_fp
            return current_fp

        def error_handler(exc):
            log.Log(
                "Error reading %s, substituting empty file." %
                (self.mirror_rp.path, ), 2)
            return io.BytesIO(b'')

        if not self.relevant_incs[-1].isreg():
            log.Log(
                """Warning: Could not restore file %s!

A regular file was indicated by the metadata, but could not be
constructed from existing increments because last increment had type
%s.  Instead of the actual file's data, an empty length file will be
created.  This error is probably caused by data loss in the
rdiff-backup destination directory, or a bug in rdiff-backup""" %


		Finds pairs under directory inc_rpath.  sub_inc_rpath will just be
		the prefix rp, while the rps in inc_list should actually exist.

		"""



class PatchITRB(rorpiter.ITRBranch):
    """Patch an rpath with the given diff iters (use with IterTreeReducer)

	The main complication here involves directories.  We have to
	finish processing the directory after what's in the directory, as
	the directory may have inappropriate permissions to alter the
	contents or the dir's mtime could change as we change the
	contents.

	This code was originally taken from backup.py.  However, because
	of different error correction requirements, it is repeated here.

	"""


		This is used when base_rp is a dir, and diff_rorp is not.

		"""



class PermissionChanger:
    """Change the permission of mirror files and directories

	The problem is that mirror files and directories may need their
	permissions changed in order to be read and listed, and then
	changed back when we are done.  This class hooks into the CachedRF
	object to know when an rp is needed.

	"""


		Do this lazily so that the permissions on the outer
		directories are fixed before we need the inner dirs.

		"""
        for i in range(len(index) - 1, -1, -1):
            if old_index[:i] == index[:i]:
                common_prefix_len = i
                break
        else:
            assert 0

        for total_len in range(common_prefix_len + 1, len(index) + 1):
            yield self.root_rp.new_index(index[:total_len])

    def finish(self):
        """Restore any remaining rps"""
        for index, rp, perms in self.open_index_list:
            rp.chmod(perms)


from . import Globals, Time, Rdiff, Hardlink, selection, rpath, \
    log, robust, metadata, statistics, TempFile, hash, longname
