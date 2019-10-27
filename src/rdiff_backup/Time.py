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
"""Provide time related exceptions and functions"""

import time
import types
import re
import sys
import calendar
from . import Globals


class TimeException(Exception):
    pass


_interval_conv_dict = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "D": 86400,
    "W": 7 * 86400,
    "M": 30 * 86400,
    "Y": 365 * 86400
}
_integer_regexp = re.compile("^[0-9]+$")
_session_regexp = re.compile("^[0-9]+B$")
_interval_regexp = re.compile("^([0-9]+)([smhDWMY])")
_genstr_date_regexp1 = re.compile(
    "^(?P<year>[0-9]{4})[-/]"
    "(?P<month>[0-9]{1,2})[-/](?P<day>[0-9]{1,2})$")
_genstr_date_regexp2 = re.compile("^(?P<month>[0-9]{1,2})[-/]"
                                  "(?P<day>[0-9]{1,2})[-/](?P<year>[0-9]{4})$")
curtime = curtimestr = None


def setcurtime(curtime=None):
    """Sets the current time in curtime and curtimestr on all systems"""
    t = curtime or time.time()
    for conn in Globals.connections:
        conn.Time.setcurtime_local(int(t))


def setcurtime_local(timeinseconds):
    """Only set the current time locally"""
    global curtime, curtimestr
    curtime, curtimestr = timeinseconds, timetostring(timeinseconds)


def setprevtime(timeinseconds):
    """Sets the previous inc time in prevtime and prevtimestr"""
    assert 0 < timeinseconds < curtime, \
        "Time %s is out of bounds" % (timeinseconds,)
    timestr = timetostring(timeinseconds)
    for conn in Globals.connections:
        conn.Time.setprevtime_local(timeinseconds, timestr)


def setprevtime_local(timeinseconds, timestr):
    """Like setprevtime but only set the local version"""
    global prevtime, prevtimestr
    prevtime, prevtimestr = timeinseconds, timestr


def timetostring(timeinseconds):
    """Return w3 datetime compliant listing of timeinseconds, or one in
	which :'s have been replaced with -'s"""
    if not Globals.use_compatible_timestamps:
        format_string = "%Y-%m-%dT%H:%M:%S"
    else:
        format_string = "%Y-%m-%dT%H-%M-%S"
    s = time.strftime(format_string, time.localtime(timeinseconds))
    return s + gettzd(timeinseconds)


def timetobytes(timeinseconds):
    return timetostring(timeinseconds).encode('ascii')


def stringtotime(timestring):
    """Return time in seconds from w3 timestring

	If there is an error parsing the string, or it doesn't look
	like a w3 datetime string, return None.

	"""






def bytestotime(timebytes):
    return stringtotime(timebytes.decode('ascii'))


def timetopretty(timeinseconds):
    """Return pretty version of time"""
    return time.asctime(time.localtime(timeinseconds))


def stringtopretty(timestring):
    """Return pretty version of time given w3 time string"""
    return timetopretty(stringtotime(timestring))


def prettytotime(prettystring):
    """Converts time like "Mon Jun 5 11:00:23" to epoch sec, or None"""
    try:
        return time.mktime(time.strptime(prettystring))
    except ValueError:
        return None


def inttopretty(seconds):


def intstringtoseconds(interval_string):
    """Convert a string expressing an interval (e.g. "4D2s") to seconds"""

    def error():
        raise TimeException("""Bad interval string "%s"

Intervals are specified like 2Y (2 years) or 2h30m (2.5 hours).  The
allowed special characters are s, m, h, D, W, M, and Y.  See the man
page for more information.
""" % interval_string)





	Expresed as [+/-]hh:mm.  For instance, PDT is -07:00 during
	dayling savings and -08:00 otherwise.  Zone coincides with what
	localtime(), etc., use.  If no argument given, use the current
	time.

	"""


def tzdtoseconds(tzd):


def cmp(time1, time2):






	The current mirror is session_num 0, the next oldest increment has
	number 1, etc.  Requires that the Globals.rbdir directory be set.

	"""
    session_times = Globals.rbdir.conn.restore.MirrorStruct \
        .get_increment_times()
    session_times.sort()
    if len(session_times) <= session_num:
        return session_times[0]  # Use oldest if too few backups
    return session_times[-session_num - 1]


def genstrtotime(timestr, curtime=None, rp=None):
    """Convert a generic time string to a time in seconds

	rp is used when the time is of the form "4B" or similar.  Then the
	times of the increments of that particular file are used.

	"""


    def error():
        raise TimeException("""Bad time string "%s"

The acceptible time strings are intervals (like "3D64s"), w3-datetime
strings, like "2002-04-26T04:22:01-07:00" (strings like
"2002-04-26T04:22:01" are also acceptable - rdiff-backup will use the
current time zone), or ordinary dates like 2/4/1997 or 2001-04-23
(various combinations are acceptable, but the month always precedes
the day).""" % timestr)


