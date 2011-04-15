"""
UserOrgRole manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class UserOrgRoleManager(ObjectManager):
    """
    Manage user roles within organizations in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'owner' : 'get_foreign_key',
            'organization' : 'get_foreign_key',
            'organization_name' : 'get_general',
            'role' : 'get_foreign_key',
            'role_name' : 'get_general',
            'parent' : 'get_foreign_key',
            'children' : 'get_many_to_one',
        })
        self.setters.update({
            'owner' : 'set_forbidden', # placeholder
            'organization' : 'set_forbidden', # placeholder
            'role' : 'set_forbidden', # placeholder
            'parent' : 'set_foreign_key',
        })
        self.my_django_model = facade.models.UserOrgRole

# vim:tabstop=4 shiftwidth=4 expandtab
