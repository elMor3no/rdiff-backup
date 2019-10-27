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
"""Generate and process aggregated backup information"""

import re
import os
import time
from functools import reduce
from . import Globals, Time, increment, log, metadata, rpath


class StatsException(Exception):
    pass


class StatsObj:
    """Contains various statistics, provide string conversion functions"""

    stat_file_attrs = ('SourceFiles', 'SourceFileSize', 'MirrorFiles',
                       'MirrorFileSize', 'NewFiles', 'NewFileSize',
                       'DeletedFiles', 'DeletedFileSize', 'ChangedFiles',
                       'ChangedSourceSize', 'ChangedMirrorSize',
                       'IncrementFiles', 'IncrementFileSize')
    stat_misc_attrs = ('Errors', 'TotalDestinationSizeChange')
    stat_time_attrs = ('StartTime', 'EndTime', 'ElapsedTime')
    stat_attrs = (
        ('Filename', ) + stat_time_attrs + stat_misc_attrs + stat_file_attrs)

    # Below, the second value in each pair is true iff the value
    # indicates a number of bytes
    stat_file_pairs = (('SourceFiles', None), ('SourceFileSize',
                                               1), ('MirrorFiles', None),
                       ('MirrorFileSize',
                        1), ('NewFiles', None), ('NewFileSize',
                                                 1), ('DeletedFiles', None),
                       ('DeletedFileSize',
                        1), ('ChangedFiles', None), ('ChangedSourceSize', 1),
                       ('ChangedMirrorSize',
                        1), ('IncrementFiles', None), ('IncrementFileSize', 1))

    # This is used in get_byte_summary_string below
    byte_abbrev_list = ((1024 * 1024 * 1024 * 1024, "TB"),
                        (1024 * 1024 * 1024, "GB"), (1024 * 1024,
                                                     "MB"), (1024, "KB"))

    def __init__(self):
        """Set attributes to None"""
        for attr in self.stat_attrs:
            self.__dict__[attr] = None

    def get_stat(self, attribute):
        """Get a statistic"""
        return self.__dict__[attribute]

    def set_stat(self, attr, value):
        """Set attribute to given value"""
        self.__dict__[attr] = value

    def increment_stat(self, attr):
        """Add 1 to value of attribute"""
        self.__dict__[attr] += 1

    def add_to_stat(self, attr, value):
        """Add value to given attribute"""
        self.__dict__[attr] += value

    def get_total_dest_size_change(self):
        """Return total destination size change

		This represents the total change in the size of the
		rdiff-backup destination directory.

		"""



class StatFileObj(StatsObj):



_active_statfileobj = None


def init_statfileobj():
    """Return new stat file object, record as active stat object"""
    global _active_statfileobj
    assert not _active_statfileobj, _active_statfileobj
    _active_statfileobj = StatFileObj()
    return _active_statfileobj


def get_active_statfileobj():


def record_error():


def process_increment(inc_rorp):



class FileStats:


		The buffer part is necessary because the GzipFile.write()
		method seems fairly slow.

		"""

