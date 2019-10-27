# Copyright 2003 Ben Escoto
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
"""Determine the capabilities of given file system

rdiff-backup needs to read and write to file systems with varying
abilities.  For instance, some file systems and not others have ACLs,
are case-sensitive, or can store ownership information.  The code in
this module tests the file system for various features, and returns an
FSAbilities object describing it.

"""

import errno
import os
from . import Globals, log, TempFile, selection, robust, SetConnections, \
    FilenameMapping, win_acls, Time


class FSAbilities:


		This method does not write to the file system at all, and
		should be run on the file system when the file system will
		only need to be read.

		Only self.acls and self.eas are set.

		"""
        assert rp.conn is Globals.local_connection
        self.root_rp = rp
        self.read_only = 1
        self.set_eas(rp, 0)
        self.set_acls(rp)
        self.set_win_acls(rp, 0)
        self.set_resource_fork_readonly(rp)
        self.set_carbonfile()
        self.set_case_sensitive_readonly(rp)
        self.set_escape_dos_devices(rp)
        self.set_escape_trailing_spaces_readonly(rp)
        return self

    def init_readwrite(self, rbdir):
        """Set variables using fs tested at rp_base.  Run locally.

		This method creates a temp directory in rp_base and writes to
		it in order to test various features.  Use on a file system
		that will be written to.

		"""


			Recurse down the directory, looking for any file that has
			a letter in it.  Return the pair (rp, [list of filenames])
			where the list is of the directory containing rp.

			"""

		can be used to obtain Finder info (creator/type)."""
        try:
            import Carbon.File
            import MacOS
        except (ImportError, AttributeError):
            self.carbonfile = 0
            return

        try:
            x = Carbon.File.FSSpec('.')
        except:
            self.carbonfile = 0
            return

        self.carbonfile = 1

    def set_resource_fork_readwrite(self, dir_rp):
        """Test for resource forks by writing to regular_file/..namedfork/rsrc"""
        assert dir_rp.conn is Globals.local_connection
        reg_rp = dir_rp.append('regfile')
        reg_rp.touch()

        s = 'test string---this should end up in resource fork'
        try:
            fp_write = open(
                os.path.join(reg_rp.path, b'..namedfork', b'rsrc'), 'wb')
            fp_write.write(s)
            assert not fp_write.close()

            fp_read = open(
                os.path.join(reg_rp.path, b'..namedfork', b'rsrc'), 'rb')
            s_back = fp_read.read()
            assert not fp_read.close()
        except (OSError, IOError):
            self.resource_forks = 0
        else:
            self.resource_forks = (s_back == s)
        reg_rp.delete()

    def set_resource_fork_readonly(self, dir_rp):
        """Test for resource fork support by testing an regular file

		Launches search for regular file in given directory.  If no
		regular file is found, resource_fork support will be turned
		off by default.

		"""
        for rp in selection.Select(dir_rp).set_iter():
            if rp.isreg():
                try:
                    rfork = rp.append(os.path.join(b'..namedfork', b'rsrc'))
                    fp = rfork.open('rb')
                    fp.read()
                    assert not fp.close()
                except (OSError, IOError):
                    self.resource_forks = 0
                    return
                self.resource_forks = 1
                return
        self.resource_forks = 0

    def set_high_perms_readwrite(self, dir_rp):
        """Test for writing high-bit permissions like suid"""
        tmpf_rp = dir_rp.append(b"high_perms_file")
        tmpf_rp.touch()
        tmpd_rp = dir_rp.append(b"high_perms_dir")
        tmpd_rp.touch()
        try:
            tmpf_rp.chmod(0o7000, 4)
            tmpf_rp.chmod(0o7777, 4)
            tmpd_rp.chmod(0o7000, 4)
            tmpd_rp.chmod(0o7777, 4)
        except (OSError, IOError):
            self.high_perms = 0
        else:
            self.high_perms = 1
        tmpf_rp.delete()
        tmpd_rp.delete()

    def set_symlink_perms(self, dir_rp):
        """Test if symlink permissions are affected by umask"""
        sym_source = dir_rp.append(b"symlinked_file1")
        sym_source.touch()
        sym_dest = dir_rp.append(b"symlinked_file2")
        try:
            sym_dest.symlink(b"symlinked_file1")
        except (OSError, AttributeError):
            self.symlink_perms = 0
        else:
            sym_dest.setdata()
            assert sym_dest.issym()
            if sym_dest.getperms() == 0o700: self.symlink_perms = 1
            else: self.symlink_perms = 0
            sym_dest.delete()
        sym_source.delete()

    def set_escape_dos_devices(self, subdir):
        """Test if DOS device files can be used as filenames.

		This test must detect if the underlying OS is Windows, whether we are
		running under Cygwin or natively. Cygwin allows these special files to
		be stat'd from any directory. Native Windows returns OSError (like
		non-Cygwin POSIX), but we can check for that using os.name.

		Note that 'con' and 'aux' have some unusual behaviors as shown below.

		os.lstat() 	 |	con			aux			prn
		-------------+-------------------------------------
		Unix		 |	OSError,2	OSError,2	OSError,2
		Cygwin/NTFS	 |	-success-	-success-	-success-
		Cygwin/FAT32 |	-success-	-HANGS-
		Native Win	 |	WinError,2	WinError,87	WinError,87
		"""
        if os.name == "nt":
            self.escape_dos_devices = 1
            return

        try:
            device_rp = subdir.append(b"con")
            if device_rp.lstat():
                self.escape_dos_devices = 1
            else:
                self.escape_dos_devices = 0
        except (OSError):
            self.escape_dos_devices = 1

    def set_escape_trailing_spaces_readwrite(self, testdir):
        """Windows and Linux/FAT32 will not preserve trailing spaces or periods.
	
		Linux/FAT32 behaves inconsistently: It will give an OSError,22 if
		os.mkdir() is called on a directory name with a space at the end, but
		will give an IOError("invalid mode") if you attempt to create a filename
		with a space at the end. However, if a period is placed at the end of
		the name, Linux/FAT32 is consistent with Cygwin and Native Windows.
		"""

        period_rp = testdir.append("foo.")
        assert not period_rp.lstat()

        tmp_rp = testdir.append("foo")
        tmp_rp.touch()
        assert tmp_rp.lstat()

        period_rp.setdata()
        if period_rp.lstat():
            self.escape_trailing_spaces = 1
        else:
            self.escape_trailing_spaces = 0

        tmp_rp.delete()

    def set_escape_trailing_spaces_readonly(self, rp):
        """Determine if directory at rp permits filenames with trailing
		spaces or periods without writing."""




def get_readonly_fsa(desc_string, rp):
    """Return an fsa with given description_string

	Will be initialized read_only with given RPath rp.  We separate
	this out into a separate function so the request can be vetted by
	the security module.

	"""
    if os.name == 'nt':
        log.Log("Hardlinks disabled by default on Windows", 4)
        SetConnections.UpdateGlobal('preserve_hardlinks', 0)
    return FSAbilities(desc_string).init_readonly(rp)


class SetGlobals:
    """Various functions for setting Globals vars given FSAbilities above

	Container for BackupSetGlobals and RestoreSetGlobals (don't use directly)

	"""

    def __init__(self, in_conn, out_conn, src_fsa, dest_fsa):
        """Just store some variables for use below"""
        self.in_conn, self.out_conn = in_conn, out_conn
        self.src_fsa, self.dest_fsa = src_fsa, dest_fsa

    def set_eas(self):
        self.update_triple(self.src_fsa.eas, self.dest_fsa.eas,
                           ('eas_active', 'eas_write', 'eas_conn'))

    def set_acls(self):
        self.update_triple(self.src_fsa.acls, self.dest_fsa.acls,
                           ('acls_active', 'acls_write', 'acls_conn'))
        if Globals.never_drop_acls and not Globals.acls_active:
            log.Log.FatalError("--never-drop-acls specified, but ACL support\n"
                               "missing from source filesystem")

    def set_win_acls(self):
        self.update_triple(
            self.src_fsa.win_acls, self.dest_fsa.win_acls,
            ('win_acls_active', 'win_acls_write', 'win_acls_conn'))

    def set_resource_forks(self):
        self.update_triple(self.src_fsa.resource_forks,
                           self.dest_fsa.resource_forks,
                           ('resource_forks_active', 'resource_forks_write',
                            'resource_forks_conn'))

    def set_carbonfile(self):
        self.update_triple(
            self.src_fsa.carbonfile, self.dest_fsa.carbonfile,
            ('carbonfile_active', 'carbonfile_write', 'carbonfile_conn'))

    def set_hardlinks(self):
        if Globals.preserve_hardlinks != 0:
            SetConnections.UpdateGlobal('preserve_hardlinks',
                                        self.dest_fsa.hardlinks)

    def set_fsync_directories(self):
        SetConnections.UpdateGlobal('fsync_directories',
                                    self.dest_fsa.fsync_dirs)

    def set_change_ownership(self):
        SetConnections.UpdateGlobal('change_ownership',
                                    self.dest_fsa.ownership)

    def set_high_perms(self):
        if not self.dest_fsa.high_perms:
            SetConnections.UpdateGlobal('permission_mask', 0o777)

    def set_symlink_perms(self):
        SetConnections.UpdateGlobal('symlink_perms',
                                    self.dest_fsa.symlink_perms)

    def set_compatible_timestamps(self):
        if Globals.chars_to_quote.find(b":") > -1:
            SetConnections.UpdateGlobal('use_compatible_timestamps', 1)
            Time.setcurtime(
                Time.curtime)  # update Time.curtimestr on all conns
            log.Log("Enabled use_compatible_timestamps", 4)


class BackupSetGlobals(SetGlobals):

		regular filename escaping. If only the destination requires it,
		then we do it. Otherwise, it is not necessary, since the files
		couldn't have been created in the first place. We also record
		whether we have done it in order to handle the case where a
		volume which was escaped is later restored by an OS that does


		Unlike most other options, the chars_to_quote setting also
		depends on the current settings in the rdiff-backup-data
		directory, not just the current fs features.

		"""


The quoting chars this session needs %r do not match
the repository settings %r listed in

%s

This may be caused when you copy an rdiff-backup repository from a
normal file system onto a windows one that cannot support the same
characters, or if you backup a case-sensitive file system onto a
case-insensitive one that previously only had case-insensitive ones
backed up onto it.

By specifying the --force option, rdiff-backup will migrate the
repository from the old quoting chars to the new ones.""" %
                    (suggested_ctq, actual_ctq, ctq_rp.get_safepath()))
        return (actual_ctq, None)  # Maintain Globals override


class RestoreSetGlobals(SetGlobals):
    """Functions for setting fsa-related globals for restore session"""

    def update_triple(self, src_support, dest_support, attr_triple):
        """Update global settings for feature based on fsa results

		This is slightly different from BackupSetGlobals.update_triple
		because (using the mirror_metadata file) rpaths from the
		source may have more information than the file system
		supports.

		"""

		rdiff-backup-data dir, just like chars_to_quote"""



class SingleSetGlobals(RestoreSetGlobals):



def backup_set_globals(rpin, force):
    """Given rps for source filesystem and repository, set fsa globals

	This should be run on the destination connection, because we may
	need to write a new chars_to_quote file.

	"""
    assert Globals.rbdir.conn is Globals.local_connection
    src_fsa = rpin.conn.fs_abilities.get_readonly_fsa('source', rpin)
    log.Log(str(src_fsa), 4)
    dest_fsa = FSAbilities('destination').init_readwrite(Globals.rbdir)
    log.Log(str(dest_fsa), 4)

    bsg = BackupSetGlobals(rpin.conn, Globals.rbdir.conn, src_fsa, dest_fsa)
    bsg.set_eas()
    bsg.set_acls()
    bsg.set_win_acls()
    bsg.set_resource_forks()
    bsg.set_carbonfile()
    bsg.set_hardlinks()
    bsg.set_fsync_directories()
    bsg.set_change_ownership()
    bsg.set_high_perms()
    bsg.set_symlink_perms()
    update_quoting = bsg.set_chars_to_quote(Globals.rbdir, force)
    bsg.set_special_escapes(Globals.rbdir)
    bsg.set_compatible_timestamps()

    if update_quoting and force:
        FilenameMapping.update_quoting(Globals.rbdir)


def restore_set_globals(rpout):
    """Set fsa related globals for restore session, given in/out rps"""
    assert rpout.conn is Globals.local_connection
    src_fsa = Globals.rbdir.conn.fs_abilities.get_readonly_fsa(
        'rdiff-backup repository', Globals.rbdir)
    log.Log(str(src_fsa), 4)
    dest_fsa = FSAbilities('restore target').init_readwrite(rpout)
    log.Log(str(dest_fsa), 4)

    rsg = RestoreSetGlobals(Globals.rbdir.conn, rpout.conn, src_fsa, dest_fsa)
    rsg.set_eas()
    rsg.set_acls()
    rsg.set_win_acls()
    rsg.set_resource_forks()
    rsg.set_carbonfile()
    rsg.set_hardlinks()
    # No need to fsync anything when restoring
    rsg.set_change_ownership()
    rsg.set_high_perms()
    rsg.set_symlink_perms()
    rsg.set_chars_to_quote(Globals.rbdir)
    rsg.set_special_escapes(Globals.rbdir)
    rsg.set_compatible_timestamps()


def single_set_globals(rp, read_only=None):
    """Set fsa related globals for operation on single filesystem"""
    if read_only:
        fsa = rp.conn.fs_abilities.get_readonly_fsa(rp.path, rp)
    else:
        fsa = FSAbilities(rp.path).init_readwrite(rp)
    log.Log(str(fsa), 4)

    ssg = SingleSetGlobals(rp.conn, fsa)
    ssg.set_eas()
    ssg.set_acls()
    ssg.set_resource_forks()
    ssg.set_carbonfile()
    if not read_only:
        ssg.set_hardlinks()
        ssg.set_change_ownership()
        ssg.set_high_perms()
        ssg.set_symlink_perms()
    ssg.set_chars_to_quote(Globals.rbdir)
    ssg.set_special_escapes(Globals.rbdir)
    ssg.set_compatible_timestamps()
