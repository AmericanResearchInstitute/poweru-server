"""
credential_type manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class CredentialTypeManager(ObjectManager):
    """
    Manage credential_types in the Power Reg system

    <pre>
    credential_type attributes:
    name          Name of the credential_type
    description   description of the credential_type
    </pre>
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'description' : 'get_general',
            'name' : 'get_general',
            'prerequisite_credential_types' : 'get_many_to_many',
            'required_achievements' : 'get_many_to_many',
            'min_required_tasks' : 'get_general',
        })
        self.setters.update({
            'description' : 'set_general',
            'name' : 'set_general',
            'prerequisite_credential_types' : 'set_many',
            'required_achievements' : 'set_many',
            'min_required_tasks' : 'set_general',
        })
        self.my_django_model = facade.models.CredentialType

    @service_method
    def create(self, auth_token, name, description):
        """
        Create a new credential_type
        
        @param name                name of the credential_type
        @param description         description of the credential_type
        @return                    a reference to the newly created credential_type
                                   struct with new primary key indexed as 'id'
        """

        c = self.my_django_model(name=name, description=description)
        c.save()
        self.authorizer.check_create_permissions(auth_token, c)
        return c

# vim:tabstop=4 shiftwidth=4 expandtab
