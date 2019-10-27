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
"""Support code for remote execution and data transfer"""

import types
import os
import tempfile
import pickle
import shutil
import traceback
import socket
import sys
import gzip


# The following EA and ACL modules may be used if available





class Connection:
    """Connection class - represent remote execution

	The idea is that, if c is an instance of this class, c.foo will
	return the object on the remote side.  For functions, c.foo will
	return a function that, when called, executes foo on the remote
	side, sending over the arguments and sending back the result.

	"""

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Simple Connection"  # override later

    def __bool__(self):
        return True


class LocalConnection(Connection):
    """Local connection

	This is a dummy connection class, so that LC.foo just evaluates to
	foo using global scope.

	"""














class ConnectionRequest:





class LowLevelPipeConnection(Connection):
    """Routines for just sending objects from one side of pipe to another

	Each thing sent down the pipe is paired with a request number,
	currently limited to be between 0 and 255.  The size of each thing
	should be less than 2^56.

	Each thing also has a type, indicated by one of the following
	characters:

	o - generic object
	i - iterator/generator of RORPs
	f - file object
	b - string
	q - quit signal
	R - RPath
	Q - QuotedRPath
	r - RORPath only
	c - PipeConnection object

	"""

    def __init__(self, inpipe, outpipe):
        """inpipe is a file-type open for reading, outpipe for writing"""
        self.inpipe = inpipe
        self.outpipe = outpipe

    def __str__(self):
        """Return string version

		This is actually an important function, because otherwise
		requests to represent this object would result in "__str__"
		being executed on the other side of the connection.

		"""


		The rpath's connection will be encoded as its conn_number.  It
		and the other information is put in a tuple.

		"""
        rpath_repr = (rpath.conn.conn_number, rpath.base, rpath.index,
                      rpath.data)
        self._write("R", pickle.dumps(rpath_repr, 1), req_num)

    def _putqrpath(self, qrpath, req_num):
        """Put a quoted rpath into the pipe (similar to _putrpath above)"""
        qrpath_repr = (qrpath.conn.conn_number, qrpath.base, qrpath.index,
                       qrpath.data)
        self._write("Q", pickle.dumps(qrpath_repr, 1), req_num)

    def _putrorpath(self, rorpath, req_num):
        """Put an rorpath into the pipe

		This is only necessary because if there is a .file attached,
		it must be excluded from the pickling

		"""
        rorpath_repr = (rorpath.index, rorpath.data)
        self._write("r", pickle.dumps(rorpath_repr, 1), req_num)

    def _putconn(self, pipeconn, req_num):
        """Put a connection into the pipe

		A pipe connection is represented just as the integer (in
		string form) of its connection number it is *connected to*.

		"""



class PipeConnection(LowLevelPipeConnection):
    """Provide server and client functions for a Pipe Connection

	Both sides act as modules that allows for remote execution.  For
	instance, self.conn.pow(2,8) will execute the operation on the
	server side.

	The only difference between the client and server is that the
	client makes the first request, and the server listens first.

	"""

    def __init__(self, inpipe, outpipe, conn_number=0):
        """Init PipeConnection

		conn_number should be a unique (to the session) integer to
		identify the connection.  For instance, all connections to the
		client have conn_number 0.  Other connections can use this
		number to route commands to the correct process.

		"""
        LowLevelPipeConnection.__init__(self, inpipe, outpipe)
        self.conn_number = conn_number
        self.unused_request_numbers = {}
        for i in range(256):
            self.unused_request_numbers[i] = None

    def __str__(self):
        return "PipeConnection %d" % self.conn_number

    def get_response(self, desired_req_num):
        """Read from pipe, responding to requests until req_num.

		Sometimes after a request is sent, the other side will make
		another request before responding to the original one.  In
		that case, respond to the request.  But return once the right
		response is given.

		"""
        while 1:
            try:
                req_num, object = self._get()
            except ConnectionQuit:
                self._put("quitting", self.get_new_req_num())
                self._close()
                return
            if req_num == desired_req_num: return object
            else:
                assert isinstance(object, ConnectionRequest)
                self.answer_request(object, req_num)

    def answer_request(self, request, req_num):
        """Put the object requested by request down the pipe"""
        del self.unused_request_numbers[req_num]
        argument_list = []
        for i in range(request.num_args):
            arg_req_num, arg = self._get()
            assert arg_req_num == req_num
            argument_list.append(arg)
        try:
            Security.vet_request(request, argument_list)
            result = eval(request.function_string)(*argument_list)
        except:
            result = self.extract_exception()
        self._put(result, req_num)
        self.unused_request_numbers[req_num] = None

    def extract_exception(self):
        """Return active exception"""
        if robust.is_routine_fatal(sys.exc_info()[1]):
            raise  # Fatal error--No logging necessary, but connection down
        if log.Log.verbosity >= 5 or log.Log.term_verbosity >= 5:
            log.Log(
                "Sending back exception %s of type %s: \n%s" %
                (sys.exc_info()[1], sys.exc_info()[0], "".join(
                    traceback.format_tb(sys.exc_info()[2]))), 5)
        return sys.exc_info()[1]

    def Server(self):
        """Start server's read eval return loop"""
        Globals.server = 1
        Globals.connections.append(self)
        log.Log("Starting server", 6)
        self.get_response(-1)

    def reval(self, function_string, *args):
        """Execute command on remote side

		The first argument should be a string that evaluates to a
		function, like "pow", and the remaining are arguments to that
		function.

		"""
        req_num = self.get_new_req_num()
        self._put(ConnectionRequest(function_string, len(args)), req_num)
        for arg in args:
            self._put(arg, req_num)
        result = self.get_response(req_num)
        self.unused_request_numbers[req_num] = None
        if isinstance(result, Exception): raise result
        elif isinstance(result, SystemExit): raise result
        elif isinstance(result, KeyboardInterrupt): raise result
        else: return result

    def get_new_req_num(self):
        """Allot a new request number and return it"""
        if not self.unused_request_numbers:
            raise ConnectionError("Exhaused possible connection numbers")
        req_num = list(self.unused_request_numbers.keys())[0]
        del self.unused_request_numbers[req_num]
        return req_num

    def quit(self):
        """Close the associated pipes and tell server side to quit"""
        assert not Globals.server
        self._putquit()
        self._get()
        self._close()

    def __getattr__(self, name):
        """Intercept attributes to allow for . invocation"""
        return EmulateCallable(self, name)


class RedirectedConnection(Connection):
    """Represent a connection more than one move away

	For instance, suppose things are connected like this: S1---C---S2.
	If Server1 wants something done by Server2, it will have to go
	through the Client.  So on S1's side, S2 will be represented by a
	RedirectedConnection.

	"""

    def __init__(self, conn_number, routing_number=0):
        """RedirectedConnection initializer

		Returns a RedirectedConnection object for the given
		conn_number, where commands are routed through the connection
		with the given routing_number.  0 is the client, so the
		default shouldn't have to be changed.

		"""







def RedirectedRun(conn_number, func, *args):
    """Run func with args on connection with conn number conn_number

	This function is meant to redirect requests from one connection to
	another, so conn_number must not be the local connection (and also
	for security reasons since this function is always made
	available).

	"""
    conn = Globals.connection_dict[conn_number]
    assert conn is not Globals.local_connection, conn
    return conn.reval(func, *args)


class EmulateCallable:
    """This is used by PipeConnection in calls like conn.os.chmod(foo)"""

    def __init__(self, connection, name):
        self.connection = connection
        self.name = name

    def __call__(self, *args):
        return self.connection.reval(*(self.name, ) + args)

    def __getattr__(self, attr_name):
        return EmulateCallable(self.connection,
                               "%s.%s" % (self.name, attr_name))


class EmulateCallableRedirected:
    """Used by RedirectedConnection in calls like conn.os.chmod(foo)"""

    def __init__(self, conn_number, routing_conn, name):
        self.conn_number, self.routing_conn = conn_number, routing_conn
        self.name = name

    def __call__(self, *args):
        return self.routing_conn.reval(
            *("RedirectedRun", self.conn_number, self.name) + args)

    def __getattr__(self, attr_name):
        return EmulateCallableRedirected(self.conn_number, self.routing_conn,
                                         "%s.%s" % (self.name, attr_name))


class VirtualFile:
    """When the client asks for a file over the connection, it gets this

	The returned instance then forwards requests over the connection.
	The class's dictionary is used by the server to associate each
	with a unique file number.

	"""





























# everything has to be available here for remote connection's use, but
# put at bottom to reduce circularities.
from . import Globals, Time, Rdiff, Hardlink, FilenameMapping, Security, \
    Main, rorpiter, selection, increment, statistics, manage, \
    iterfile, rpath, robust, restore, manage, backup, connection, \
    TempFile, SetConnections, librsync, log, regress, fs_abilities, \
    eas_acls, user_group, compare

try:
    from . import win_acls
except ImportError:
    pass

Globals.local_connection = LocalConnection()
Globals.connections.append(Globals.local_connection)
# Following changed by server in SetConnections
Globals.connection_dict[0] = Globals.local_connection
