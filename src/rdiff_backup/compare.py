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
"""Perform various kinds of comparisons.

For instance, full-file compare, compare by hash, and metadata-only
compare.  This uses elements of the backup and restore modules.

"""

import os
from . import Globals, restore, rorpiter, log, backup, rpath, hash, robust


def Compare(src_rp, mirror_rp, inc_rp, compare_time):
    """Compares metadata in src_rp dir with metadata in mirror_rp at time"""
    repo_side = mirror_rp.conn.compare.RepoSide
    data_side = src_rp.conn.compare.DataSide

    repo_iter = repo_side.init_and_get_iter(mirror_rp, inc_rp, compare_time)
    return_val = print_reports(data_side.compare_fast(repo_iter))
    repo_side.close_rf_cache()
    return return_val


def Compare_hash(src_rp, mirror_rp, inc_rp, compare_time):
    """Compare files at src_rp with repo at compare_time

	Note metadata differences, but also check to see if file data is
	different.  If two regular files have the same size, hash the
	source and compare to the hash presumably already present in repo.

	"""
    repo_side = mirror_rp.conn.compare.RepoSide
    data_side = src_rp.conn.compare.DataSide

    repo_iter = repo_side.init_and_get_iter(mirror_rp, inc_rp, compare_time)
    return_val = print_reports(data_side.compare_hash(repo_iter))
    repo_side.close_rf_cache()
    return return_val


def Compare_full(src_rp, mirror_rp, inc_rp, compare_time):
    """Compare full data of files at src_rp with repo at compare_time

	Like Compare_hash, but do not rely on hashes, instead copy full
	data over.

	"""
    repo_side = mirror_rp.conn.compare.RepoSide
    data_side = src_rp.conn.compare.DataSide

    src_iter = data_side.get_source_select()
    attached_repo_iter = repo_side.attach_files(src_iter, mirror_rp, inc_rp,
                                                compare_time)
    report_iter = data_side.compare_full(src_rp, attached_repo_iter)
    return_val = print_reports(report_iter)
    repo_side.close_rf_cache()
    return return_val


def Verify(mirror_rp, inc_rp, verify_time):


def print_reports(report_iter):
    """Given an iter of CompareReport objects, print them to screen"""
    assert not Globals.server
    changed_files_found = 0
    for report in report_iter:
        changed_files_found = 1
        indexpath = report.index and b"/".join(report.index) or b"."
        print("%s: %s" % (report.reason, os.fsdecode(indexpath)))

    if not changed_files_found:
        log.Log("No changes found.  Directory matches archive data.", 3)
    return changed_files_found


def get_basic_report(src_rp, repo_rorp, comp_data_func=None):
    """Compare src_rp and repo_rorp, return CompareReport

	comp_data_func should be a function that accepts (src_rp,
	repo_rorp) as arguments, and return 1 if they have the same data,
	0 otherwise.  If comp_data_func is false, don't compare file data,
	only metadata.

	"""



class RepoSide(restore.MirrorStruct):
    """On the repository side, comparing is like restoring"""

    @classmethod
    def init_and_get_iter(cls, mirror_rp, inc_rp, compare_time):
        """Return rorp iter at given compare time"""
        cls.set_mirror_and_rest_times(compare_time)
        cls.initialize_rf_cache(mirror_rp, inc_rp)
        return cls.subtract_indicies(cls.mirror_base.index,
                                     cls.get_mirror_rorp_iter())

    @classmethod
    def attach_files(cls, src_iter, mirror_rp, inc_rp, compare_time):
        """Attach data to all the files that need checking

		Return an iterator of repo rorps that includes all the files
		that may have changed, and has the fileobj set on all rorps
		that need it.

		"""



class DataSide(backup.SourceStruct):



class CompareReport:
    """When two files don't match, this tells you how they don't match

	This is necessary because the system that is doing the actual
	comparing may not be the one printing out the reports.  For speed
	the compare information can be pipelined back to the client
	connection as an iter of CompareReports.

	"""
    # self.file is added so that CompareReports can masquerate as
    # RORPaths when in an iterator, and thus get pipelined.
    file = None

    def __init__(self, index, reason):
        self.index = index
        self.reason = reason
