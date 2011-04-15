"""
credential manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class CredentialManager(ObjectManager):
    """
    Manage credentials in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'authority' : 'get_general',
            'credential_type' : 'get_foreign_key',
            'date_assigned' : 'get_time',
            'date_expires' : 'get_time',
            'date_granted' : 'get_time',
            'date_started' : 'get_time',
            'serial_number' : 'get_general',
            'status' : 'get_general',
            'user' : 'get_foreign_key',
        })
        self.setters.update({
            'authority' : 'set_general',
            'credential_type' : 'set_foreign_key',
            'date_assigned' : 'set_time',
            'date_expires' : 'set_time',
            'date_granted' : 'set_time',
            'date_started' : 'set_time',
            'serial_number' : 'set_general',
            'status' : 'set_general',
            'user' : 'set_foreign_key',
        })
        self.my_django_model = facade.models.Credential

    @service_method
    def create(self, auth_token, user_id, credential_type_id, optional_attributes=None):
        """
        Create a new credential
        
        @param user_id              primary key of User who owns the credential
        @param credential_type_id   a credential_type key that the credential should be
        @param optional_attributes  dictionary of optional attributes for the credential
        @return                     a reference to the newly created credential
        """

        if optional_attributes is None:
            optional_attributes = {}

        u = self._find_by_id(user_id, facade.models.User)
        c = self.my_django_model(user=u, owner=u)
        optional_attributes.update({'credential_type' : credential_type_id})
        facade.subsystems.Setter(auth_token, self, c, optional_attributes)
        c.save()
        self.authorizer.check_create_permissions(auth_token, c)
        return c

# vim:tabstop=4 shiftwidth=4 expandtab
