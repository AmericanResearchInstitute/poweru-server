# This code should preserve coherency between the database's and the cache's
# view of settings if there is only one writer active at a time (and an
# unlimited number of readers). It will not do so if there are several
# concurrent writers. This should not be a problem in practice, since only
# the site admin can write.
from __future__ import with_statement

import threading
import cPickle
from django.core.cache import cache

import facade
from pr_services import exceptions as pr_exceptions
from pr_services.pr_models import DBSetting
from pr_services.rpc.service import service_method

allsettings = dict()
allsettings_lock = threading.Lock()

class DBSettingBase(object):
    def __init__(self, name, group=''):
        self.name = name
        self.group = group
        self.cache_key = 'dbsetting_' + name
        with allsettings_lock:
            if allsettings.has_key(name):
                if allsettings[name].__class__ != self.__class__:
                    raise TypeError('DBSetting redeclared as a different type')
                if allsettings[name].group != group:
                    raise TypeError('DBSetting redeclared in a different group')
            else:
                allsettings[name] = self

    def _get_value(self):
        pv = cache.get(self.cache_key)
        if not pv:
            pv = str(DBSetting.objects.get(name=self.name).pickled_value)
            cache.add(self.cache_key, pv)
        return cPickle.loads(pv)

    def _coerce_value(self, new_value):
        return new_value

    def _set_value(self, new_value):
        pv = cPickle.dumps(self._coerce_value(new_value))
        dbv = DBSetting.objects.get_or_create(name=self.name)[0]
        dbv.pickled_value = pv
        dbv.save()
        cache.set(self.cache_key, pv)

    value = property(_get_value, _set_value)


class DBSettingString(DBSettingBase):
    type_name = 'string'
    def _coerce_value(self, new_value):
        return str(new_value)

class DBSettingLong(DBSettingBase):
    type_name = 'long'
    def _coerce_value(self, new_value):
        return long(new_value)

class DBSettingBool(DBSettingBase):
    type_name = 'bool'
    def _coerce_value(self, new_value):
        return bool(new_value)


class DBSettingManager(object):
    @service_method
    def get(self, auth_token, name):
        facade.subsystems.Authorizer().check_arbitrary_permissions(auth_token,
            'access_db_settings')
        with allsettings_lock:
            setting = allsettings.get(name)
        if not setting:
            raise pr_exceptions.ObjectNotFoundException('DBSetting')
        return {
            'type' : setting.type_name,
            'value' : setting.value,
            'group' : setting.group,
        }

    @service_method
    def set(self, auth_token, name, new_value):
        facade.subsystems.Authorizer().check_arbitrary_permissions(auth_token,
            'access_db_settings')
        with allsettings_lock:
            setting = allsettings.get(name)
        if not setting:
            raise pr_exceptions.ObjectNotFoundException('DBSetting')
        setting.value = new_value

    @service_method
    def get_all(self, auth_token):
        facade.subsystems.Authorizer().check_arbitrary_permissions(auth_token,
            'access_db_settings')
        retval = {}
        with allsettings_lock:
            for name, setting in allsettings.iteritems():
                retval[name] = {
                    'type' : setting.type_name,
                    'value' : setting.value,
                    'group' : setting.group,
                }
        return retval

    @service_method
    def set_many(self, auth_token, value_map):
        facade.subsystems.Authorizer().check_arbitrary_permissions(auth_token,
            'access_db_settings')
        # we do this in 2 phases because if there's an error the DB changes
        # will be rolled back, but the cache changes won't, so we want to
        # make sure we catch any invalid names before we start making changes
        settings = {}
        with allsettings_lock:
            for name in value_map.iterkeys():
                setting = allsettings.get(name)
                if not setting:
                    raise pr_exceptions.ObjectNotFoundException('DBSetting')
                settings[name] = setting
        for name, value in value_map.iteritems():
            settings[name].value = value
