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
"""Manage logging, displaying and recording messages with required verbosity"""

import time
import sys
import traceback
import types
import re
from . import Globals, rpath


class LoggerError(Exception):
    pass


class Logger:


		rpath.conn will write to the file, and the others will pass
		write commands off to it.

		"""


		message can be a string, which is logged as-is, or a function,
		which is then called and should return the string to be
		logged.  We do it this way in case producing the string would
		take a significant amount of CPU.
		
		"""


		The main worry with this function is that something in here
		will create more network traffic, which will spiral to
		infinite regress.  So, for instance, logging must only be done
		to the terminal, because otherwise the log file may be remote.

		"""


		If only_terminal is None, log normally.  If it is 1, then only
		log to disk if log file is local (self.log_file_open = 1).  If
		it is 2, don't log to disk at all.

		"""



Log = Logger()


class ErrorLog:
    """Log each recoverable error in error_log file

	There are three types of recoverable errors:  ListError, which
	happens trying to list a directory or stat a file, UpdateError,
	which happen when trying to update a changed file, and
	SpecialFileError, which happen when a special file cannot be
	created.  See the error policy file for more info.

	"""

