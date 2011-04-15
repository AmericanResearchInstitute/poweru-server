"""
OrgRole manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class OrgRoleManager(ObjectManager):
    """
    Manage roles that users can have in organizations in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'name' : 'get_general',
            'organizations' : 'get_many_to_many',
            'users' : 'get_many_to_many',
            'user_org_roles' : 'get_many_to_one',
        })
        self.setters.update({
            'name' : 'set_general',
            'organizations' : 'set_many',
            'users' : 'set_many',
        })
        self.my_django_model = facade.models.OrgRole

    @service_method
    def create(self, auth_token, name):
        """
        Create a new OrgRole
        
        @param name                 name of the OrgRole

        @return                     a reference to the newly created OrgRole
        """

        o = self.my_django_model.objects.create(name=name)
        self.authorizer.check_create_permissions(auth_token, o)
        return o

# vim:tabstop=4 shiftwidth=4 expandtab
