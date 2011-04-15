"""
DomainAffiliation manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class DomainAffiliationManager(ObjectManager):
    """
    Manage domain affiliations in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'default' : 'get_general',
            'domain' : 'get_foreign_key',
            'may_log_me_in' : 'get_general',
            'user' : 'get_foreign_key',
            'username' : 'get_general',
        })
        self.setters.update({
            'default' : 'set_general',
            'domain' : 'set_foreign_key',
            'may_log_me_in' : 'set_general',
            'user' : 'set_foreign_key',
            'username' : 'set_general',
        })
        self.my_django_model = facade.models.DomainAffiliation

    @service_method
    def create(self, auth_token, user, domain, username, optional_attributes = None):
        """
        Create a new DomainAffiliation
        
        @param user
        @param optional_attributes  Optional dict which only supports one value indexed as 'authentication_ip'

        @return                     a reference to the newly created DomainAffiliation
        """
        user_object = self._find_by_id(user, facade.models.User)
        domain_object = self._find_by_id(domain, facade.models.Domain)

        o = self.my_django_model(user=user_object, domain=domain_object, username=username)

        if optional_attributes is not None:
            for attribute in ['default', 'may_log_me_in']:
                if attribute in optional_attributes:
                    setattr(o, attribute, optional_attributes[attribute])
        o.save()
        self.authorizer.check_create_permissions(auth_token, o)
        return o

# vim:tabstop=4 shiftwidth=4 expandtab
