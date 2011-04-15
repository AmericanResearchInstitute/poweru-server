"""
Domain manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
from pr_services.utils import Utils
import facade

class DomainManager(ObjectManager):
    """
    Manage domains in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'authentication_ip' : 'get_general',
            'name' : 'get_general',
            'users' : 'get_many_to_one',
        })
        self.setters.update({
            'authentication_ip' : 'set_general',
            'authentication_password_hash' : 'set_forbidden', # placeholder
            'name' : 'set_general',
        })
        self.my_django_model = facade.models.Domain

    @service_method
    def create(self, auth_token, name, optional_attributes = None):
        """
        Create a new Domain
        
        @param name                 name of the Domain
        @param optional_attributes  Optional dict which only supports one value indexed as 'authentication_ip'

        @return                     a reference to the newly created Domain
        """

        o = self.my_django_model(name=name)
        if optional_attributes is not None and'authentication_ip' in optional_attributes:
            o.authentication_ip = optional_attributes['authentication_ip']
        o.save()
        self.authorizer.check_create_permissions(auth_token, o)
        return o

    @service_method
    def change_password(self, auth_token, domain, new_password):
        d = self._find_by_id(domain)
        new_hash = Utils._hash(new_password, 'SHA-512')
        self.authorizer.check_update_permissions(auth_token, d, {'authentication_password_hash' : new_hash})
        d.authentication_password_hash = new_hash
        d.save()

# vim:tabstop=4 shiftwidth=4 expandtab
