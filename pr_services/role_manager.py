"""
Role manager class
"""

from object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class RoleManager(ObjectManager):
    """
    Manage Roles in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.setters.update({
            'name' : 'set_general',
            'ac_check_methods' : 'set_many',
            'acl' : 'set_acl',
        })
        self.getters.update({
            'name' : 'get_general',
            'ac_check_methods' : 'get_many_to_many',
            'acl' : 'get_acl',
        })
        self.my_django_model = facade.models.Role

    @service_method
    def create(self, auth_token, name):
        """
        Create a new Role
        
        @param name               name of the Role
        @return                   a reference to the newly created Role
                                  struct with new primary key indexed as 'id'
        """

        r = self.my_django_model(name=name)
        r.save()
        self.authorizer.check_create_permissions(auth_token, r)
        self.authorizer._load_acls()
        
        return r

# vim:tabstop=4 shiftwidth=4 expandtab
