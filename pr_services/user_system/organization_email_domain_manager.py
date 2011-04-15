"""
OrgEmailDomain manager class

@author Chris Church <cchurch@americanri.com>
@copyright Copyright 2011 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class OrgEmailDomainManager(ObjectManager):
    """
    Manage mappings between email domain and automatic organization and role
    assignment.
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'email_domain' : 'get_general',
            'organization' : 'get_foreign_key',
            'role' : 'get_foreign_key',
            'effective_role' : 'get_foreign_key',
            'effective_role_name' : 'get_general',
        })
        self.setters.update({
            'email_domain' : 'set_general',
            'organization' : 'set_foreign_key',
            'role' : 'set_foreign_key',
        })
        self.my_django_model = facade.models.OrgEmailDomain

    @service_method
    def create(self, auth_token, email_domain, organization, role=None):
        """
        Create a new OrgEmailDomain mapping

        @param email_domain     domain name to look for in user's email address
        @param organization     organization to be assigned
        @param role             role to be assigned within organization

        @return                 a reference to the newly created OrgEmailDomain
        """

        organization_object = self._find_by_id(organization, facade.models.Organization)
        role_object = self._find_by_id(role, facade.models.OrgRole) if role else None

        obj = self.my_django_model.objects.create(email_domain=email_domain, organization=organization_object, role=role_object)
        self.authorizer.check_create_permissions(auth_token, obj)
        return obj

# vim:tabstop=4 shiftwidth=4 expandtab
