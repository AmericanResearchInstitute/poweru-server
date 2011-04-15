"""
This modules deals with time and date conversion

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

import datetime
import iso8601
import exceptions
import sys

class UTC(datetime.tzinfo):
    """
    time zone (tzinfo) class for UTC
    """
    
    def utcoffset(self, dt):
        return datetime.timedelta(0)
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return datetime.timedelta(0)

def iso8601_to_datetime(time):
    """
    Convert an ISO8601 string to a python datetime object.
    
    @param time       ISO8601 string
    @return           python datetime object without tzinfo
    """

    try:
        time_stamp = iso8601.parse(time)
    except ValueError:
        raise exceptions.DatetimeConversionError()
    else:
       return datetime.datetime.utcfromtimestamp(time_stamp)

def is_iso8601(time):
    """
    Return true if time is a valid iso8601 time value.
    
    @param time   the time we wish to validate
    @return       boolean False if it is invalid, else True
    """

    try:
        iso8601.parse(time)
    except ValueError:
        return False
    else:
        return True

# vim:tabstop=4 shiftwidth=4 expandtab
