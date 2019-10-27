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
"""Start (and end) here - read arguments, set global settings, etc."""


from .log import Log, LoggerError, ErrorLog
from . import Globals, Time, SetConnections, selection, robust, rpath, \
    manage, backup, connection, restore, FilenameMapping, \
    Security, Hardlink, regress, C, fs_abilities, statistics, compare

action = None
create_full_path = None
remote_cmd, remote_schema = None, None
force = None
select_opts = []
select_files = []
user_mapping_filename, group_mapping_filename, preserve_numerical_ids = \
        None, None, None

# These are global because they are set while we are trying to figure
# whether to restore or to backup
restore_root, restore_index, restore_root_set = None, None, 0
return_val = None  # Set to cause exit code to be specified value


def parse_cmdlineoptions(arglist):


def check_action():


def final_set_action(rps):


def commandline_error(message):
    Log.FatalError(
        "%s\nSee the rdiff-backup manual page for more information." % message)


def misc_setup(rps):
    """Set default change ownership flag, umask, relay regexps"""
    os.umask(0o77)
    Time.setcurtime(Globals.current_time)
    SetConnections.UpdateGlobal("client_conn", Globals.local_connection)
    Globals.postset_regexp('no_compression_regexp',
                           Globals.no_compression_regexp_string)
    for conn in Globals.connections:
        conn.robust.install_signal_handlers()
        conn.Hardlink.initialize_dictionaries()


def init_user_group_mapping(destination_conn):


def take_action(rps):
    """Do whatever action says"""
    if action == "server":
        connection.PipeConnection(sys.stdin.buffer, sys.stdout.buffer).Server()
        sys.exit(0)
    elif action == "backup":
        Backup(rps[0], rps[1])
    elif action == "calculate-average":
        CalculateAverage(rps)
    elif action == "check-destination-dir":
        CheckDest(rps[0])
    elif action.startswith("compare"):
        Compare(action, rps[0], rps[1])
    elif action == "list-at-time":
        ListAtTime(rps[0])
    elif action == "list-changed-since":
        ListChangedSince(rps[0])
    elif action == "list-increments":
        ListIncrements(rps[0])
    elif action == 'list-increment-sizes':
        ListIncrementSizes(rps[0])
    elif action == "remove-older-than":
        RemoveOlderThan(rps[0])
    elif action == "restore":
        Restore(*rps)
    elif action == "restore-as-of":
        Restore(rps[0], rps[1], 1)
    elif action == "test-server":
        SetConnections.TestConnections(rps)
    elif action == "verify":
        Verify(rps[0])
    else:
        raise AssertionError("Unknown action " + action)


def cleanup():


def error_check_Main(arglist):
    """Run Main on arglist, suppressing stack trace for routine errors"""
    try:
        Main(arglist)
    except SystemExit:
        raise
    except (Exception, KeyboardInterrupt) as exc:
        errmsg = robust.is_routine_fatal(exc)
        if errmsg:
            Log.exception(2, 6)
            Log.FatalError(errmsg)
        else:
            Log.exception(2, 2)
            raise


def Main(arglist):


def Backup(rpin, rpout):


def backup_quoted_rpaths(rpout):
    """Get QuotedRPath versions of important RPaths.  Return rpout"""
    global incdir
    SetConnections.UpdateGlobal('rbdir',
                                FilenameMapping.get_quotedrpath(Globals.rbdir))
    incdir = FilenameMapping.get_quotedrpath(incdir)
    return FilenameMapping.get_quotedrpath(rpout)


def backup_set_select(rpin):
    """Create Select objects on source connection"""
    if rpin.conn.os.name == 'nt':
        Log("Symbolic links excluded by default on Windows", 4)
        select_opts.append(("--exclude-symbolic-links", None))
    rpin.conn.backup.SourceStruct.set_source_select(rpin, select_opts,
                                                    *select_files)


def backup_check_dirs(rpin, rpout):


def check_failed_initial_backup():
    """Returns true if it looks like initial backup failed."""
    if Globals.rbdir.lstat():
        rbdir_files = Globals.rbdir.listdir()
        mirror_markers = [
            x for x in rbdir_files if x.startswith(b"current_mirror")
        ]
        error_logs = [x for x in rbdir_files if x.startswith(b"error_log")]
        metadata_mirrors = [
            x for x in rbdir_files if x.startswith(b"mirror_metadata")
        ]
        # If we have no current_mirror marker, and the increments directory
        # is empty, we most likely have a failed backup.
        return not mirror_markers and len(error_logs) <= 1 and \
          len(metadata_mirrors) <= 1
    return False


def fix_failed_initial_backup():
    """Clear Globals.rbdir after a failed initial backup"""
    Log("Found interrupted initial backup. Removing...", 2)
    rbdir_files = Globals.rbdir.listdir()
    # Try to delete the increments dir first
    if b'increments' in rbdir_files:
        rbdir_files.remove(b'increments')
        rp = Globals.rbdir.append(b'increments')
        try:
            rp.conn.rpath.delete_dir_no_files(rp)
        except rpath.RPathException:
            Log("Increments dir contains files.", 4)
            return
        except Security.Violation:
            Log("Server doesn't support resuming.", 2)
            return

    for file_name in rbdir_files:
        rp = Globals.rbdir.append_path(file_name)
        if not rp.isdir():  # Only remove files, not folders
            rp.delete()


def backup_set_rbdir(rpin, rpout):
    """Initialize data dir and logging"""
    global incdir
    try:
        incdir = Globals.rbdir.append_path(b"increments")
    except IOError as exc:
        if exc.errno == errno.EACCES:
            print("\n")
            Log.FatalError("Could not begin backup due to\n%s" % exc)
        else:
            raise

    assert rpout.lstat(), (rpout.get_safepath(), rpout.lstat())
    if rpout.isdir() and not rpout.listdir():  # rpout is empty dir
        try:
            rpout.chmod(0o700)  # just make sure permissions aren't too lax
        except OSError:
            Log("Cannot change permissions on target directory.", 2)
    elif not Globals.rbdir.lstat() and not force:
        Log.FatalError("""Destination directory

%s

exists, but does not look like a rdiff-backup directory.  Running
rdiff-backup like this could mess up what is currently in it.  If you
want to update or overwrite it, run rdiff-backup with the --force
option.""" % rpout.get_safepath())
    elif check_failed_initial_backup():
        fix_failed_initial_backup()

    if not Globals.rbdir.lstat():
        try:
            Globals.rbdir.mkdir()
        except (OSError, IOError) as exc:
            Log.FatalError("""Could not create rdiff-backup directory

%s

due to

%s

Please check that the rdiff-backup user can create files and directories in the
destination directory: %s""" % (Globals.rbdir.get_safepath(), exc,
                                rpout.get_safepath()))
    SetConnections.UpdateGlobal('rbdir', Globals.rbdir)


def backup_warn_if_infinite_regress(rpin, rpout):

source directory '%s'.  This could cause an infinite regress.  You
may need to use the --exclude option.""" % (rpout.get_safepath(),
                                            rpin.get_safepath()), 2)


def backup_get_mirrortime():


def backup_final_init(rpout):
    """Open the backup log and the error log, create increments dir"""
    global prevtime, incdir
    if Log.verbosity > 0:
        Log.open_logfile(Globals.rbdir.append("backup.log"))
    checkdest_if_necessary(rpout)
    prevtime = backup_get_mirrortime()
    if prevtime >= Time.curtime:
        Log.FatalError(
            """Time of Last backup is not in the past.  This is probably caused
by running two backups in less than a second.  Wait a second and try again.""")


def backup_touch_curmirror_local(rpin, rpout):
    """Make a file like current_mirror.time.data to record time

	When doing an incremental backup, this should happen before any
	other writes, and the file should be removed after all writes.
	That way we can tell whether the previous session aborted if there
	are two current_mirror files.

	When doing the initial full backup, the file can be created after
	everything else is in place.

	"""
    mirrorrp = Globals.rbdir.append(b'.'.join(
        map(os.fsencode, (b"current_mirror", Time.curtimestr, "data"))))
    Log("Writing mirror marker %s" % mirrorrp.get_safepath(), 6)
    try:
        pid = os.getpid()
    except:
        pid = "NA"
    mirrorrp.write_string("PID %s\n" % (pid, ))
    mirrorrp.fsync_with_dir()


def backup_remove_curmirror_local():
    """Remove the older of the current_mirror files.  Use at end of session"""
    assert Globals.rbdir.conn is Globals.local_connection
    curmir_incs = restore.get_inclist(Globals.rbdir.append(b"current_mirror"))
    assert len(curmir_incs) == 2
    if curmir_incs[0].getinctime() < curmir_incs[1].getinctime():
        older_inc = curmir_incs[0]
    else:
        older_inc = curmir_incs[1]

    C.sync()  # Make sure everything is written before curmirror is removed
    older_inc.delete()


def backup_close_statistics(end_time):
    """Close out the tracking of the backup statistics.
	
	Moved to run at this point so that only the clock of the system on which
	rdiff-backup is run is used (set by passing in time.time() from that
	system). Use at end of session.

	"""



def Restore(src_rp, dest_rp, restore_as_of=None):
    """Main restoring function

	Here src_rp should be the source file (either an increment or
	mirror file), dest_rp should be the target rp to be written.

	"""
    if not restore_root_set and not restore_set_root(src_rp):
        Log.FatalError("Could not find rdiff-backup repository at %s" %
                       src_rp.get_safepath())
    restore_check_paths(src_rp, dest_rp, restore_as_of)
    try:
        dest_rp.conn.fs_abilities.restore_set_globals(dest_rp)
    except IOError as exc:
        if exc.errno == errno.EACCES:
            print("\n")
            Log.FatalError("Could not begin restore due to\n%s" % exc)
        else:
            raise
    init_user_group_mapping(dest_rp.conn)
    src_rp = restore_init_quoting(src_rp)
    restore_check_backup_dir(restore_root, src_rp, restore_as_of)
    inc_rpath = Globals.rbdir.append_path(b'increments', restore_index)
    if restore_as_of:
        try:
            time = Time.genstrtotime(restore_timestr, rp=inc_rpath)
        except Time.TimeException as exc:
            Log.FatalError(str(exc))
    else:
        time = src_rp.getinctime()
    restore_set_select(restore_root, dest_rp)
    restore_start_log(src_rp, dest_rp, time)
    try:
        restore.Restore(
            restore_root.new_index(restore_index), inc_rpath, dest_rp, time)
    except IOError as exc:
        if exc.errno == errno.EACCES:
            print("\n")
            Log.FatalError("Could not complete restore due to\n%s" % exc)
        else:
            raise
    else:
        Log("Restore finished", 4)


def restore_init_quoting(src_rp):


def restore_set_select(mirror_rp, target):
    """Set the selection iterator on both side from command line args

	We must set both sides because restore filtering is different from
	select filtering.  For instance, if a file is excluded it should
	not be deleted from the target directory.

	The BytesIO stuff is because filelists need to be read and then
	duplicated, because we need two copies of them now.

	"""

    def fp2string(fp):
        buf = fp.read()
        assert not fp.close()
        return buf

    select_data = list(map(fp2string, select_files))
    if select_opts:
        mirror_rp.conn.restore.MirrorStruct.set_mirror_select(
            target, select_opts, *list(map(io.BytesIO, select_data)))
        target.conn.restore.TargetStruct.set_target_select(
            target, select_opts, *list(map(io.BytesIO, select_data)))


def restore_start_log(rpin, target, time):


Try restoring from an increment file (the filenames look like
"foobar.2001-09-01T04:49:04-07:00.diff").""" % src_rp.get_safepath())

    result = checkdest_need_check(mirror_root)
    if result is None:
        Log.FatalError("%s does not appear to be an rdiff-backup directory." %
                       Globals.rbdir.get_safepath())
    elif result == 1:
        Log.FatalError(
            "Previous backup to %s seems to have failed.\nRerun rdiff-backup "
            "with --check-destination-dir option to revert directory "
            "to state before unsuccessful session." %
            mirror_root.get_safepath())


def restore_set_root(rpin):
    """Set data dir, restore_root and index, or return None if fail

	The idea here is to keep backing up on the path until we find
	a directory that contains "rdiff-backup-data".  That is the
	mirror root.  If the path from there starts
	"rdiff-backup-data/increments*", then the index is the
	remainder minus that.  Otherwise the index is just the path
	minus the root.

	All this could fail if the increment file is pointed to in a
	funny way, using symlinks or somesuch.

	"""



def ListIncrements(rp):
    """Print out a summary of the increments and their times"""
    rp = require_root_set(rp, 1)
    restore_check_backup_dir(restore_root)
    mirror_rp = restore_root.new_index(restore_index)
    inc_rpath = Globals.rbdir.append_path(b'increments', restore_index)
    incs = restore.get_inclist(inc_rpath)
    mirror_time = restore.MirrorStruct.get_mirror_time()
    if Globals.parsable_output:
        print(manage.describe_incs_parsable(incs, mirror_time, mirror_rp))
    else:
        print(manage.describe_incs_human(incs, mirror_time, mirror_rp))


def require_root_set(rp, read_only):
    """Make sure rp is or is in a valid rdiff-backup dest directory.

	Also initializes fs_abilities (read or read/write) and quoting and
	return quoted rp if necessary.

	"""


def ListIncrementSizes(rp):
    """Print out a summary of the increments """
    rp = require_root_set(rp, 1)
    print(manage.ListIncrementSizes(restore_root, restore_index))


def CalculateAverage(rps):
    """Print out the average of the given statistics files"""
    statobjs = [statistics.StatsObj().read_stats_from_rp(rp) for rp in rps]
    average_stats = statistics.StatsObj().set_to_average(statobjs)
    print(average_stats.get_stats_logstring(
        "Average of %d stat files" % len(rps)))


def RemoveOlderThan(rootrp):



def rot_check_time(time_string):
    """Check remove older than time_string, return time in seconds"""
    try:
        time = Time.genstrtotime(time_string)
    except Time.TimeException as exc:
        Log.FatalError(str(exc))

    times_in_secs = [
        inc.getinctime() for inc in restore.get_inclist(
            Globals.rbdir.append_path(b"increments"))
    ]
    times_in_secs = [t for t in times_in_secs if t < time]
    if not times_in_secs:
        Log(
            "No increments older than %s found, exiting." %
            (Time.timetopretty(time), ), 3)
        return None

    times_in_secs.sort()
    inc_pretty_time = "\n".join(map(Time.timetopretty, times_in_secs))
    if len(times_in_secs) > 1 and not force:
        Log.FatalError(
            "Found %d relevant increments, dated:\n%s"
            "\nIf you want to delete multiple increments in this way, "
            "use the --force." % (len(times_in_secs), inc_pretty_time))
    if len(times_in_secs) == 1:
        Log("Deleting increment at time:\n%s" % inc_pretty_time, 3)
    else:
        Log("Deleting increments at times:\n%s" % inc_pretty_time, 3)
    return times_in_secs[-1] + 1  # make sure we don't delete current increment


def rot_require_rbdir_base(rootrp):
    """Make sure pointing to base of rdiff-backup dir"""
    if restore_index != ():
        Log.FatalError("Increments for directory %s cannot be removed "
                       "separately.\nInstead run on entire directory %s." %
                       (rootrp.get_safepath(), restore_root.get_safepath()))


def ListChangedSince(rp):
    """List all the files under rp that have changed since restoretime"""
    rp = require_root_set(rp, 1)
    try:
        rest_time = Time.genstrtotime(restore_timestr)
    except Time.TimeException as exc:
        Log.FatalError(str(exc))
    mirror_rp = restore_root.new_index(restore_index)
    inc_rp = mirror_rp.append_path(b"increments", restore_index)
    for rorp in rp.conn.restore.ListChangedSince(mirror_rp, inc_rp, rest_time):
        # This is a hack, see restore.ListChangedSince for rationale
        print(rorp.index[0])


def ListAtTime(rp):
    """List files in archive under rp that are present at restoretime"""
    rp = require_root_set(rp, 1)
    try:
        rest_time = Time.genstrtotime(restore_timestr)
    except Time.TimeException as exc:
        Log.FatalError(str(exc))
    mirror_rp = restore_root.new_index(restore_index)
    inc_rp = mirror_rp.append_path(b"increments", restore_index)
    for rorp in rp.conn.restore.ListAtTime(mirror_rp, inc_rp, rest_time):
        print(rorp.get_indexpath())


def Compare(compare_type, src_rp, dest_rp, compare_time=None):
    """Compare metadata in src_rp with metadata of backup session

	Prints to stdout whenever a file in the src_rp directory has
	different metadata than what is recorded in the metadata for the
	appropriate session.

	Session time is read from restore_timestr if compare_time is None.

	"""



def CheckDest(dest_rp):
    """Check the destination directory, """
    dest_rp = require_root_set(dest_rp, 0)
    need_check = checkdest_need_check(dest_rp)
    if need_check is None:
        Log.FatalError(
            "No destination dir found at %s" % dest_rp.get_safepath())
    elif need_check == 0:
        Log.FatalError(
            "Destination dir %s does not need checking" %
            dest_rp.get_safepath(),
            no_fatal_message=1,
            errlevel=0)
    init_user_group_mapping(dest_rp.conn)
    dest_rp.conn.regress.Regress(dest_rp)


def checkdest_need_check(dest_rp):


The rdiff-backup data directory
%s
exists, but we cannot find a valid current_mirror marker.  You can
avoid this message by removing the rdiff-backup-data directory;
however any data in it will be lost.

Probably this error was caused because the first rdiff-backup session
into a new directory failed.  If this is the case it is safe to delete
the rdiff-backup-data directory because there is no important
information in it.

""" % (Globals.rbdir.get_safepath(), ))
    elif len(curmir_incs) == 1:
        return 0
    else:
        if not force:
            try:
                curmir_incs[0].conn.regress.check_pids(curmir_incs)
            except (OSError, IOError) as exc:
                Log.FatalError("Could not check if rdiff-backup is currently"
                               "running due to\n%s" % exc)
        assert len(curmir_incs) == 2, "Found too many current_mirror incs!"
        return 1


def checkdest_if_necessary(dest_rp):
    """Check the destination dir if necessary.

	This can/should be run before an incremental backup.

	"""
    need_check = checkdest_need_check(dest_rp)
    if need_check == 1:
        Log(
            "Previous backup seems to have failed, regressing "
            "destination now.", 2)
        try:
            dest_rp.conn.regress.Regress(dest_rp)
        except Security.Violation:
            Log.FatalError("Security violation while attempting to regress "
                           "destination, perhaps due to --restrict-read-only "
                           "or --restrict-update-only.")
