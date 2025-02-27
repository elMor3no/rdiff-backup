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
"""Parse args and setup connections

The functions in this module are used once by Main to parse file
descriptions like bescoto@folly.stanford.edu:/usr/bin/ls and to set up
the related connections.

"""

import os
import sys
import subprocess
from .log import Log
from . import Globals, connection, rpath

# This is the schema that determines how rdiff-backup will open a
# pipe to the remote system.  If the file is given as A::B, %s will
# be substituted with A in the schema.
__cmd_schema = b'ssh -C %s rdiff-backup --server'
__cmd_schema_no_compress = b'ssh %s rdiff-backup --server'

# This is a list of remote commands used to start the connections.
# The first is None because it is the local connection.
__conn_remote_cmds = [None]


class SetConnectionsException(Exception):
    pass


def get_cmd_pairs(arglist, remote_schema=None, remote_cmd=None):
    """Map the given file descriptions into command pairs

	Command pairs are tuples cmdpair with length 2.  cmdpair[0] is
	None iff it describes a local path, and cmdpair[1] is the path.

	"""


def cmdpair2rp(cmd_pair):


def desc2cmd_pairs(desc_pair):


def parse_file_desc(file_desc):
    """Parse file description returning pair (host_info, filename)

	In other words, bescoto@folly.stanford.edu::/usr/bin/ls =>
	("bescoto@folly.stanford.edu", "/usr/bin/ls").  The
	complication is to allow for quoting of : by a \.  If the
	string is not separated by :, then the host_info is None.

	"""

    def check_len(i):
        if i >= len(file_desc):
            raise SetConnectionsException(
                "Unexpected end to file description %s" % file_desc)

    host_info_list, i, last_was_quoted = [], 0, None
    file_desc = os.fsencode(
        file_desc)  # paths and similar must always be bytes
    while 1:
        if i == len(file_desc):
            return (None, file_desc)

        if file_desc[i] == ord(
                '\\'):  # byte[n] is the numerical value hence ord
            i = i + 1
            check_len(i)
            last_was_quoted = 1
        elif (file_desc[i] == ord(":") and i > 0
              and file_desc[i - 1] == ord(":") and not last_was_quoted):
            host_info_list.pop()  # Remove last colon from name
            break
        else:
            last_was_quoted = None
        host_info_list.append(file_desc[i:i + 1])
        i = i + 1

    check_len(i + 1)
    return (b"".join(host_info_list), file_desc[i + 1:])


def fill_schema(host_info):
    """Fills host_info into the schema and returns remote command"""
    try:
        return __cmd_schema % host_info
    except TypeError:
        Log.FatalError("Invalid remote schema:\n\n%a\n" % __cmd_schema)


def init_connection(remote_cmd):
    """Run remote_cmd, register connection, and then return it

	If remote_cmd is None, then the local connection will be
	returned.  This also updates some settings on the remote side,
	like global settings, its connection number, and verbosity.

	"""


def check_connection_version(conn, remote_cmd):
    """Log warning if connection has different version"""
    try:
        remote_version = conn.Globals.get('version')
    except connection.ConnectionError as exception:
        Log.FatalError("""%s

Couldn't start up the remote connection by executing

    %a

Remember that, under the default settings, rdiff-backup must be
installed in the PATH on the remote system.  See the man page for more
information on this.  This message may also be displayed if the remote
version of rdiff-backup is quite different from the local version (%s).""" %
                       (exception, remote_cmd, Globals.version))
    except OverflowError as exc:
        Log.FatalError(
            """Integer overflow while attempting to establish the 
remote connection by executing

    %s

Please make sure that nothing is printed (e.g., by your login shell) when this
command executes. Try running this command:

    %a
	
which should only print out the text: rdiff-backup <version>""" %
            (remote_cmd, remote_cmd.replace(b"--server", b"--version")))

    if remote_version != Globals.version:
        Log(
            "Warning: Local version %s does not match remote version %s." %
            (Globals.version, remote_version), 2)


def init_connection_routing(conn, conn_number, remote_cmd):





def init_connection_settings(conn):
    """Tell new conn about log settings and updated globals"""
    conn.log.Log.setverbosity(Log.verbosity)
    conn.log.Log.setterm_verbosity(Log.term_verbosity)
    for setting_name in Globals.changed_settings:
        conn.Globals.set(setting_name, Globals.get(setting_name))


def init_connection_remote(conn_number):
    """Run on server side to tell self that have given conn_number"""
    Globals.connection_number = conn_number
    Globals.local_connection.conn_number = conn_number
    Globals.connection_dict[0] = Globals.connections[1]
    Globals.connection_dict[conn_number] = Globals.local_connection


def add_redirected_conn(conn_number):
    """Run on server side - tell about redirected connection"""
    Globals.connection_dict[conn_number] = \
        connection.RedirectedConnection(conn_number)


def UpdateGlobal(setting_name, val):
    """Update value of global variable across all connections"""
    for conn in Globals.connections:
        conn.Globals.set(setting_name, val)


def BackupInitConnections(reading_conn, writing_conn):
    """Backup specific connection initialization"""
    reading_conn.Globals.set("isbackup_reader", 1)
    writing_conn.Globals.set("isbackup_writer", 1)
    UpdateGlobal("backup_reader", reading_conn)
    UpdateGlobal("backup_writer", writing_conn)


def CloseConnections():
    """Close all connections.  Run by client"""
    assert not Globals.server
    for conn in Globals.connections:
        conn.quit()
    del Globals.connections[1:]  # Only leave local connection
    Globals.connection_dict = {0: Globals.local_connection}
    Globals.backup_reader = Globals.isbackup_reader = \
       Globals.backup_writer = Globals.isbackup_writer = None


def TestConnections(rpaths):


def test_connection(conn_number, rp):
    """Test connection.  conn_number 0 is the local connection"""
    print("Testing server started by: ", __conn_remote_cmds[conn_number])
    conn = Globals.connections[conn_number]
    try:
        assert conn.Globals.get('current_time') is None
        try:
            assert type(conn.os.getuid()) is int
        except AttributeError:  # Windows doesn't support os.getuid()
            assert type(conn.os.listdir(rp.path)) is list
        version = conn.Globals.get('version')
    except:
        sys.stderr.write("Server tests failed\n")
        raise
    if not version == Globals.version:
        print("""Server may work, but there is a version mismatch:
Local version: %s
Remote version: %s

In general, an attempt is made to guarantee compatibility only between
different minor versions of the same stable series.  For instance, you
should expect 0.12.4 and 0.12.7 to be compatible, but not 0.12.7
and 0.13.3, nor 0.13.2 and 0.13.4.
""" % (Globals.version, version))
    else:
        print("Server OK")
