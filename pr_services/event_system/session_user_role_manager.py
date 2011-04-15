"""
SessionUserRole manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class SessionUserRoleManager(ObjectManager):
    """
    Manage SessionUserRoles in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'session_user_role_requirements' : 'get_many_to_one',
            'name' : 'get_general',
        })
        self.setters.update({
            'session_user_role_requirements' : 'set_many',
            'name' : 'set_general',
        })
        self.my_django_model = facade.models.SessionUserRole

    @service_method
    def create(self, auth_token, name, optional_parameters=None):
        """
        Create a new SessionUserRole

        Optional parameters include:
          url     URL for a website
        
        @param name                   Name for this session user role
        @param optional_parameters    Dictionary of optional parameter names and values
        """

        if optional_parameters is None:
            optional_parameters = {}

        e = self.my_django_model(name = name)
        if optional_parameters:
            facade.subsystems.Setter(auth_token, self, e, optional_parameters)
        e.save()
        self.authorizer.check_create_permissions(auth_token, e)
        return e

# vim:tabstop=4 shiftwidth=4 expandtab
