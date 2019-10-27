# Copyright 2008 Fred Gansevles <fred@betterbe.com>
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

import re
from . import C, metadata, rorpiter, rpath, log

try:
    from win32security import *
    import pywintypes
except ImportError:
    GROUP_SECURITY_INFORMATION = 0
    OWNER_SECURITY_INFORMATION = 0
    DACL_SECURITY_INFORMATION = 0

    pywintypes = None


class ACL:


def Record2WACL(record):
    acl = ACL()
    acl.from_string(record)
    return acl


def WACL2Record(wacl):
    return str(wacl)


class WACLExtractor(metadata.FlatExtractor):


class WinAccessControlListFile(metadata.FlatFile):
    """Store/retrieve ACLs from extended_attributes file"""
    _prefix = b"win_access_control_lists"
    _extractor = WACLExtractor
    _object_to_record = staticmethod(WACL2Record)


def join_wacl_iter(rorp_iter, wacl_iter):

def rpath_acl_win_get(rpath):
    acl = ACL()
    acl.load_from_rp(rpath)
    return str(acl)


rpath.win_acl_get = rpath_acl_win_get


def rpath_get_blank_win_acl(index):
    acl = ACL(index)
    return str(acl)


rpath.get_blank_win_acl = rpath_get_blank_win_acl


def rpath_set_win_acl(rp, acl_str):
    acl = ACL()
    acl.from_string(acl_str)
    acl.write_to_rp(rp)


rpath.write_win_acl = rpath_set_win_acl


def init_acls():
    # A process that tries to read or write a SACL needs
    # to have and enable the SE_SECURITY_NAME privilege.
    # And inorder to backup/restore, the SE_BACKUP_NAME and
    # SE_RESTORE_NAME privileges are needed.
    import win32api
    try:
        hnd = OpenProcessToken(win32api.GetCurrentProcess(),
                               TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY)
    except win32api.error as exc:
        log.Log("Warning: unable to open Windows process token: %s" % exc, 5)
        return
    try:
        try:
            lpv = lambda priv: LookupPrivilegeValue(None, priv)
            # enable the SE_*_NAME privileges
            SecurityName = lpv(SE_SECURITY_NAME)
            AdjustTokenPrivileges(
                hnd, False, [(SecurityName, SE_PRIVILEGE_ENABLED),
                             (lpv(SE_BACKUP_NAME), SE_PRIVILEGE_ENABLED),
                             (lpv(SE_RESTORE_NAME), SE_PRIVILEGE_ENABLED)])
        except win32api.error as exc:
            log.Log("Warning: unable to enable SE_*_NAME privileges: %s" % exc,
                    5)
            return
        for name, enabled in GetTokenInformation(hnd, TokenPrivileges):
            if name == SecurityName and enabled:
                # now we *may* access the SACL (sigh)
                ACL.flags |= SACL_SECURITY_INFORMATION
                break
    finally:
        win32api.CloseHandle(hnd)
