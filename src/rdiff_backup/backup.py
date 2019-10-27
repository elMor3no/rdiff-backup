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
"""High level functions for mirroring and mirror+incrementing"""

import errno


def Mirror(src_rpath, dest_rpath):
    """Turn dest_rpath into a copy of src_rpath"""
    log.Log(
        "Starting mirror %s to %s" % (src_rpath.get_safepath(),
                                      dest_rpath.get_safepath()), 4)
    SourceS = src_rpath.conn.backup.SourceStruct
    DestS = dest_rpath.conn.backup.DestinationStruct

    source_rpiter = SourceS.get_source_select()
    DestS.set_rorp_cache(dest_rpath, source_rpiter, 0)
    dest_sigiter = DestS.get_sigs(dest_rpath)
    source_diffiter = SourceS.get_diffs(dest_sigiter)
    DestS.patch(dest_rpath, source_diffiter)


def Mirror_and_increment(src_rpath, dest_rpath, inc_rpath):
    """Mirror + put increments in tree based at inc_rpath"""
    log.Log(
        "Starting increment operation %s to %s" % (src_rpath.get_safepath(),
                                                   dest_rpath.get_safepath()),
        4)
    SourceS = src_rpath.conn.backup.SourceStruct
    DestS = dest_rpath.conn.backup.DestinationStruct

    source_rpiter = SourceS.get_source_select()
    DestS.set_rorp_cache(dest_rpath, source_rpiter, 1)
    dest_sigiter = DestS.get_sigs(dest_rpath)
    source_diffiter = SourceS.get_diffs(dest_sigiter)
    DestS.patch_and_increment(dest_rpath, source_diffiter, inc_rpath)


class SourceStruct:
    """Hold info used on source side when backing up"""
    _source_select = None  # will be set to source Select iterator

    @classmethod
    def set_source_select(cls, rpath, tuplelist, *filelists):
        """Initialize select object using tuplelist

		Note that each list in filelists must each be passed as
		separate arguments, so each is recognized as a file by the
		connection.  Otherwise we will get an error because a list
		containing files can't be pickled.

		Also, cls._source_select needs to be cached so get_diffs below
		can retrieve the necessary rps.

		"""



class DestinationStruct:


		If metadata file doesn't exist, select all files on
		destination except rdiff-backup-data directory.

		"""


		for_increment should be true if we are mirror+incrementing,
		false if we are just mirroring.

		"""
        dest_iter = cls.get_dest_select(baserp, for_increment)
        collated = rorpiter.Collate2Iters(source_iter, dest_iter)
        cls.CCPP = CacheCollatedPostProcess(
            collated, Globals.pipeline_max_length * 4, baserp)
        # pipeline len adds some leeway over just*3 (to and from and back)

    @classmethod
    def get_sigs(cls, dest_base_rpath):
        """Yield signatures of any changed destination files

		If we are backing up across a pipe, we must flush the pipeline
		every so often so it doesn't get congested on destination end.

		"""



class CacheCollatedPostProcess:


	This is necessary for three reasons:

	1.  The patch function may need the original source_rorp or
	    dest_rp information, which is not present in the diff it
	    receives.

	2.  The metadata must match what is stored in the destination
	    directory.  If there is an error, either we do not update the
	    dest directory for that file and the old metadata is used, or
	    the file is deleted on the other end..  Thus we cannot write
	    any metadata until we know the file has been procesed
	    correctly.

	3.  We may lack permissions on certain destination directories.
	    The permissions of these directories need to be relaxed before
	    we enter them to computer signatures, and then reset after we
	    are done patching everything inside them.

	4.  We need some place to put hashes (like SHA1) after computing
	    them and before writing them to the metadata.

	The class caches older source_rorps and dest_rps so the patch
	function can retrieve them if necessary.  The patch function can
	also update the processed correctly flag.  When an item falls out
	of the cache, we assume it has been processed, and write the
	metadata for it.

	"""

    def __init__(self, collated_iter, cache_size, dest_root_rp):
        """Initialize new CCWP."""
        self.iter = collated_iter  # generates (source_rorp, dest_rorp) pairs
        self.cache_size = cache_size
        self.dest_root_rp = dest_root_rp

        self.statfileobj = statistics.init_statfileobj()
        if Globals.file_statistics: statistics.FileStats.init()
        self.metawriter = metadata.ManagerObj.GetWriter()

        # the following should map indicies to lists
        # [source_rorp, dest_rorp, changed_flag, success_flag, increment]

        # changed_flag should be true if the rorps are different, and

        # success_flag should be 1 if dest_rorp has been successfully
        # updated to source_rorp, and 2 if the destination file is
        # deleted entirely.  They both default to false (0).

        # increment holds the RPath of the increment file if one
        # exists.  It is used to record file statistics.

        self.cache_dict = {}
        self.cache_indicies = []

        # Contains a list of pairs (destination_rps, permissions) to
        # be used to reset the permissions of certain directories
        # after we're finished with them
        self.dir_perms_list = []

        # Contains list of (index, (source_rorp, diff_rorp)) pairs for
        # the parent directories of the last item in the cache.
        self.parent_list = []

    def __iter__(self):
        return self

    def __next__(self):
        """Return next (source_rorp, dest_rorp) pair.  StopIteration passed"""
        source_rorp, dest_rorp = next(self.iter)
        self.pre_process(source_rorp, dest_rorp)
        index = source_rorp and source_rorp.index or dest_rorp.index
        self.cache_dict[index] = [source_rorp, dest_rorp, 0, 0, None]
        self.cache_indicies.append(index)

        if len(self.cache_indicies) > self.cache_size: self.shorten_cache()
        return source_rorp, dest_rorp

    def pre_process(self, source_rorp, dest_rorp):
        """Do initial processing on source_rorp and dest_rorp

		It will not be clear whether source_rorp and dest_rorp have
		errors at this point, so don't do anything which assumes they
		will be backed up correctly.

		"""
        if Globals.preserve_hardlinks and source_rorp:
            Hardlink.add_rorp(source_rorp, dest_rorp)
        if (dest_rorp and dest_rorp.isdir() and Globals.process_uid != 0
                and dest_rorp.getperms() % 0o1000 < 0o700):
            self.unreadable_dir_init(source_rorp, dest_rorp)

    def unreadable_dir_init(self, source_rorp, dest_rorp):
        """Initialize an unreadable dir.

		Make it readable, and if necessary, store the old permissions
		in self.dir_perms_list so the old perms can be restored.

		"""


		This method keeps parent directories in the secondary parent
		cache until all their children have expired from the main
		cache.  This is necessary because we may realize we need a
		parent directory's information after we have processed many
		subfiles.

		"""


		The point of this is to write statistics and metadata.

		changed will be true if the files have changed.  success will
		be true if the files have been successfully updated (this is
		always false for un-changed files).

		"""



class PatchITRB(rorpiter.ITRBranch):
    """Patch an rpath with the given diff iters (use with IterTreeReducer)

	The main complication here involves directories.  We have to
	finish processing the directory after what's in the directory, as
	the directory may have inappropriate permissions to alter the
	contents or the dir's mtime could change as we change the
	contents.

	"""


		Returns true if able to write new as desired, false if
		UpdateError or similar gets in the way.

		"""


		Returns 1 if normal success, 2 if special file is written,
		whether or not it is successful.  This is because special
		files either fail with a SpecialFileError, or don't need to be
		compared.

		"""
        if diff_rorp.isspecial():
            self.write_special(diff_rorp, new)
            rpath.copy_attribs(diff_rorp, new)
            return 2

        report = robust.check_common_error(self.error_handler, rpath.copy,
                                           (diff_rorp, new))
        if isinstance(report, hash.Report):
            self.CCPP.update_hash(diff_rorp.index, report.sha1_digest)
            return 1
        return report != 0  # if == 0, error_handler caught something

    def patch_diff_to_temp(self, basis_rp, diff_rorp, new):
        """Apply diff_rorp to basis_rp, write output in new"""
        assert diff_rorp.get_attached_filetype() == 'diff'
        report = robust.check_common_error(
            self.error_handler, Rdiff.patch_local, (basis_rp, diff_rorp, new))
        if isinstance(report, hash.Report):
            self.CCPP.update_hash(diff_rorp.index, report.sha1_digest)
            return 1
        return report != 0  # if report == 0, error

    def matches_cached_rorp(self, diff_rorp, new_rp):
        """Return true if new_rp matches cached src rorp

		This is a final check to make sure the temp file just written
		matches the stats which we got earlier.  If it doesn't it
		could confuse the regress operation.  This is only necessary
		for regular files.

		"""


		This is used when base_rp is a dir, and diff_rorp is not.
		Returns 1 for success or 0 for failure

		"""



class IncrementITRB(PatchITRB):
    """Patch an rpath with the given diff iters and write increments

	Like PatchITRB, but this time also write increments.

	"""


