"""
Backend Info service class.
"""

import datetime
import os
import subprocess
import time

from django.conf import settings
from pr_services.rpc.service import service_method

class LocalTimezone(datetime.tzinfo):
    """
    A class capturing the platform's idea of local time.
    From: http://docs.python.org/library/datetime.html
    """

    ZERO = datetime.timedelta(0)
    STDOFFSET = datetime.timedelta(seconds = -time.timezone)
    DSTOFFSET = datetime.timedelta(seconds = -time.altzone) if time.daylight else STDOFFSET
    DSTDIFF = DSTOFFSET - STDOFFSET

    def utcoffset(self, dt):
        return self.DSTOFFSET if self._isdst(dt) else self.STDOFFSET

    def dst(self, dt):
        return self.DSTDIFF if self._isdst(dt) else self.ZERO

    def tzname(self, dt):
        return time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, -1)
        stamp = time.mktime(tt)
        tt = time.localtime(stamp)
        return tt.tm_isdst > 0

local_timezone = LocalTimezone()

class BackendInfo(object):
    """
    This class provides information about the backend software revision and
    date/time settings. Implements #280 and #1850.
    """

    @service_method
    def get_time_zone(self):
        """
        This method can be used by the front end to fetch the current server
        TIME_ZONE setting.
        
        @return current TIME_ZONE setting
        @rtype  str
        """
        return str(settings.TIME_ZONE)

    @service_method
    def get_current_timestamp(self):
        """
        This method can be used by the front end to fetch the current server
        date and time.
        
        @return ISO8601 formatted date and time string with timezone offset
        @rtype  str
        """
        return datetime.datetime.now(local_timezone).isoformat()

    @service_method
    def get_revision(self):
        """
        This method can be used by the front end to fetch the Subversion
        revision number of the backend software.
        
        @return revision number of backend code
        @rtype  str
        """
        if not hasattr(self, '_revision'):
            self._revision = 'exported'
            try:
                self._revision = subprocess.Popen(["svnversion", "-n"],
                    cwd=settings.PROJECT_ROOT,
                    stdout=subprocess.PIPE).communicate()[0].strip()
            except OSError:
                pass
            if self._revision == 'exported':
                try:
                    self._revision = file(os.path.join(settings.PROJECT_ROOT,
                        'svn_revision'), 'rb').read().strip()
                except IOError:
                    pass
        return self._revision

# vim:tabstop=4 shiftwidth=4 expandtab
