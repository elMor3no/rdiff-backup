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
"""Functions to make sure remote requests are kosher"""

import sys
import tempfile
import types
from . import Globals, Main, rpath, log


class Violation(Exception):
    """Exception that indicates an improper request has been received"""
    pass


# This will store the list of functions that will be honored from
# remote connections.
allowed_requests = None

# This stores the list of global variables that the client can not
# set on the server.
disallowed_server_globals = ["server", "security_level", "restrict_path"]

# Some common file commands we may want to check to make sure they are
# in the right directory.  Any commands accessing files that could be
# added to allowed_requests must be here.
#
# The keys are files request, the value is the index of the argument
# taking a file.
file_requests = {
    'os.listdir': 0,
    'rpath.make_file_dict': 0,
    'os.chmod': 0,
    'os.chown': 0,
    'os.remove': 0,
    'os.removedirs': 0,
    'os.rename': 0,
    'os.renames': 0,
    'os.rmdir': 0,
    'os.unlink': 0,
    'os.utime': 0,
    'os.lchown': 0,
    'os.link': 1,
    'os.symlink': 1,
    'os.mkdir': 0,
    'os.makedirs': 0,
    'rpath.delete_dir_no_files': 0
}


def initialize(action, cmdpairs):
    """Initialize allowable request list and chroot"""
    global allowed_requests
    set_security_level(action, cmdpairs)
    set_allowed_requests(Globals.security_level)


def reset_restrict_path(rp):
    """Reset restrict path to be within rpath"""
    assert rp.conn is Globals.local_connection
    Globals.restrict_path = rp.normalize().path


def set_security_level(action, cmdpairs):
    """If running client, set security level and restrict_path

	To find these settings, we must look at the action to see what is
	supposed to happen, and then look at the cmdpairs to see what end
	the client is on.

	"""


def set_allowed_requests(sec_level):
    """Set the allowed requests list using the security level"""
    global allowed_requests
    l = [
        "VirtualFile.readfromid", "VirtualFile.closebyid", "Globals.get",
        "Globals.is_not_None", "Globals.get_dict_val",
        "log.Log.open_logfile_allconn", "log.Log.close_logfile_allconn",
        "Log.log_to_file", "FilenameMapping.set_init_quote_vals_local",
        "FilenameMapping.set_init_quote_vals", "Time.setcurtime_local",
        "SetConnections.add_redirected_conn", "RedirectedRun",
        "sys.stdout.write", "robust.install_signal_handlers"
    ]
    if (sec_level == "read-only" or sec_level == "update-only"
            or sec_level == "all"):
        l.extend([
            "rpath.make_file_dict", "os.listdir", "rpath.ea_get",
            "rpath.acl_get", "rpath.setdata_local", "log.Log.log_to_file",
            "os.getuid", "rpath.gzip_open_local_read", "rpath.open_local_read",
            "Hardlink.initialize_dictionaries", "user_group.uid2uname",
            "user_group.gid2gname"
        ])
    if sec_level == "read-only" or sec_level == "all":
        l.extend([
            "fs_abilities.get_readonly_fsa",
            "restore.MirrorStruct.get_increment_times",
            "restore.MirrorStruct.set_mirror_and_rest_times",
            "restore.MirrorStruct.set_mirror_select",
            "restore.MirrorStruct.initialize_rf_cache",
            "restore.MirrorStruct.close_rf_cache",
            "restore.MirrorStruct.get_diffs", "restore.ListChangedSince",
            "restore.ListAtTime", "backup.SourceStruct.get_source_select",
            "backup.SourceStruct.set_source_select",
            "backup.SourceStruct.get_diffs",
            "compare.RepoSide.init_and_get_iter",
            "compare.RepoSide.close_rf_cache", "compare.RepoSide.attach_files",
            "compare.DataSide.get_source_select",
            "compare.DataSide.compare_fast", "compare.DataSide.compare_hash",
            "compare.DataSide.compare_full", "compare.Verify"
        ])
    if sec_level == "update-only" or sec_level == "all":
        l.extend([
            "log.Log.open_logfile_local", "log.Log.close_logfile_local",
            "log.ErrorLog.open", "log.ErrorLog.isopen", "log.ErrorLog.close",
            "backup.DestinationStruct.set_rorp_cache",
            "backup.DestinationStruct.get_sigs",
            "backup.DestinationStruct.patch_and_increment",
            "Main.backup_touch_curmirror_local",
            "Main.backup_remove_curmirror_local",
            "Main.backup_close_statistics", "regress.check_pids",
            "Globals.ITRB.increment_stat", "statistics.record_error",
            "log.ErrorLog.write_if_open", "fs_abilities.backup_set_globals"
        ])
    if sec_level == "all":
        l.extend([
            "os.mkdir", "os.chown", "os.lchown", "os.rename", "os.unlink",
            "os.remove", "os.chmod", "os.makedirs",
            "rpath.delete_dir_no_files", "backup.DestinationStruct.patch",
            "restore.TargetStruct.get_initial_iter",
            "restore.TargetStruct.patch",
            "restore.TargetStruct.set_target_select",
            "fs_abilities.restore_set_globals",
            "fs_abilities.single_set_globals", "regress.Regress",
            "manage.delete_earlier_than_local"
        ])
    if Globals.server:
        l.extend([
            "SetConnections.init_connection_remote", "log.Log.setverbosity",
            "log.Log.setterm_verbosity", "Time.setprevtime_local",
            "Globals.postset_regexp_local",
            "backup.SourceStruct.set_session_info",
            "backup.DestinationStruct.set_session_info",
            "user_group.init_user_mapping", "user_group.init_group_mapping"
        ])
    allowed_requests = {}
    for req in l:
        allowed_requests[req] = None


def raise_violation(reason, request, arglist):
    """Raise a security violation about given request"""
    raise Violation(
        "\nWARNING: Security Violation!\n"
        "%s for function: %s\n"
        "with arguments: %s\n" % (reason, request.function_string, arglist))


def vet_request(request, arglist):



def vet_filename(request, arglist):
    """Check to see if file operation is within the restrict_path"""
    i = file_requests[request.function_string]
    if len(arglist) <= i:
        raise_violation("Argument list shorter than %d" % i + 1, request,
                        arglist)
    filename = arglist[i]
    if not (isinstance(filename, bytes) or isinstance(filename, str)):
        raise_violation("Argument %d doesn't look like a filename" % i,
                        request, arglist)

    _vet_rpath(
        rpath.RPath(Globals.local_connection, filename), request, arglist)


def _vet_rpath(rp, request, arglist):

