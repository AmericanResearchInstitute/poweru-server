from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class CustomActionManager(ObjectManager):
    """
    Manage CustomAction
    """

    def __init__(self):
        """constructor"""

        ObjectManager.__init__(self)
        self.getters.update({
            'name' : 'get_general',
            'description' : 'get_general',
            'function_name' : 'get_general',
        })
        self.setters.update({
            'name' : 'set_general',
            'description' : 'set_general',
            'function_name' : 'set_general',
        })
        self.my_django_model = facade.models.CustomAction
        self.setter = facade.subsystems.Setter

    @service_method
    def create(self, auth_token, name, description, function_name):
        """
        Create a new CustomAction

        @param name             human-readable name
        @param description      description of what it does
        @param function_name    name of the function that actually does the work.

        @return                 a reference to the newly create CustomAction
        """

        blame = self.blame_manager.create(auth_token)
        new_custom_action = self.my_django_model.objects.create(name=name,
                description=description, function_name=function_name,
                blame=blame)

        self.authorizer.check_create_permissions(auth_token, new_custom_action)

        return new_custom_action

# vim:tabstop=4 shiftwidth=4 expandtab
