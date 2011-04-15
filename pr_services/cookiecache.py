"""
Manage authorization data that is stored in memcache,
as well as in the database.
"""

from django.conf import settings

import memcache
import facade

class CookieCache(object):
    """A proxy object designed to ease managing authorization data 
    stored in memcached
    
    The docs are weak right now, and I'm working on them, but I wanted
    to get this checked in. --smyers
    
    To use, instantiate with an auth token, modify the paths attribute
    as desired, and then save. paths is a list objects, so use list methods.
    
    Example:
    cc = CookieCache(auth_token)
    cc.paths.append('/auth/path')
    cc.paths.remove('/old/auth/path')
    cc.save()
    
    This is pretty rough right now, and apache doesn't really give a crap
    about things like SCRIPT_PATH, so all the paths are relative to the
    site root. Error handling is currently lacking. Fortunately, memcache
    is a simple thing."""

    def __init__(self, auth_token):
        #: Needed by CookieCache auth module to set REMOTE_USER in web server
        self._username = auth_token.user.username

        #: session_id is used as the memcache key
        self._session_id = str(auth_token.session_id)

        #: Our Client object; MEMCACHED_ADDRS must be a list of host:port entries
        self._memcache_client = memcache.Client(settings.MEMCACHED_ADDRS)

        self.update()

    def _get_memcache_string(self):
        """Shortens the memcache get line considerably"""
        memcache_string = self._memcache_client.get(self._session_id)
        
        # try the database if we didn't find what we wanted in memcache
        if memcache_string is None:
            try:
                cached_cookie = facade.models.CachedCookie.objects.get(key=self._session_id)
                memcache_string = cached_cookie.value
            except facade.models.CachedCookie.DoesNotExist:
                pass
        
        return memcache_string

    def _memcache_string_as_dict(self, memcache_string=None):
        """returns the memcache string as python dict"""
        memcache_dict = {}

        if memcache_string is None:
            memcache_string = self._get_memcache_string()

        for line in memcache_string.split('\r\n'):
            if line == '':
                # All newlines, no substance. Moving on!
                continue

            key, value = line.split('=', 1)
            value_list = value.split(':')
            memcache_dict[key] = value_list
        
        return memcache_dict

    def _memcache_dict_as_string(self, memcache_dict):
        memcache_string = ''
        for key, value_list in memcache_dict.items():
            # list(set(listobj)) for uniqueness, prevents repeats in cache
            uniq_value_list = list(set(value_list))
            item_string = '%s=%s\r\n' % (key, ':'.join(uniq_value_list))
            memcache_string = '%s%s' % (memcache_string, item_string)

        return str(memcache_string)

    def save(self):
        """Writes the current object's state to memcached
        
        Raises a RuntimeWarning if memcache set() fails."""
        memcache_dict = {}
        memcache_dict['username'] = [self._username]
        memcache_dict['paths'] = self.paths
        
        key = self._session_id
        value = self._memcache_dict_as_string(memcache_dict)
        
        try:
            cached_cookie = facade.models.CachedCookie.objects.get(key=key)
            cached_cookie.value = value
            cached_cookie.save()
        except facade.models.CachedCookie.DoesNotExist:
            facade.models.CachedCookie.objects.create(key=key, value=value)
        
        # memcache set() will return True on success, and 0 on failure. Nice.
        if self._memcache_client.set(key, value) == 0:
            raise RuntimeWarning, 'memcache set failed. Is memcached running?'
        
    def update(self):
        """Sync this object with memcache data, populating memcache if necessary"""
        memcache_string = self._get_memcache_string()

        if memcache_string is None:
            # memcache is empty, 
            self.paths = []
            self.save()
        else:
            memcache_dict = self._memcache_string_as_dict()
            self.paths = memcache_dict['paths']

    def delete(self):
        try:
            cached_cookie = facade.models.CachedCookie.objects.get(key=self._session_id)
            cached_cookie.delete()
        except facade.models.CachedCookie.DoesNotExist:
            pass
        
        self._memcache_client.delete(self._session_id)

# vim:tabstop=4 shiftwidth=4 expandtab
