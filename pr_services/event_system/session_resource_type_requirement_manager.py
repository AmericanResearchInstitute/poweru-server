"""
SessionResourceTypeRequirement manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class SessionResourceTypeRequirementManager(ObjectManager):
    """
    Manage SessionResourceTypeRequirements in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'session' : 'get_foreign_key',
            'max' : 'get_general',
            'min' : 'get_general',
            'resource_type' : 'get_foreign_key',
            'resources' : 'get_many_to_many',
        })
        self.setters.update({
            'session' : 'set_foreign_key',
            'max' : 'set_general',
            'min' : 'set_general',
            'resource_type' : 'set_foreign_key',
            'resources' : 'set_many',
        })
        self.my_django_model = facade.models.SessionResourceTypeRequirement

    @service_method
    def create(self, auth_token, session_id, resource_type_id, min, max, resource_ids=None):
        """
        Create a new SessionResourceTypeRequirement
        
        @param session_id         Primary key for an session
        @param resource_type_id   Primary key for an resource_type
        @param min                Minimum number required
        @param max                Maximum number allowed
        @param resource_ids       Array of resource foreign keys
        @return                   A reference to the newly created SessionResourceTypeRequirement
        """

        if resource_ids is None:
            resource_ids = []

        session_instance = self._find_by_id(session_id, facade.models.Session)
        resource_type_instance = self._find_by_id(resource_type_id, facade.models.ResourceType)
        e = self.my_django_model(session = session_instance,
                resource_type=resource_type_instance, min=min, max=max)
        # We must save so that we can get a primary key, and thus establish many-to-many
        # relationships below
        e.save()
        if resource_ids:
            facade.subsystems.Setter(auth_token, self, e, {'resources' : { 'add' : resource_ids}})
        self.authorizer.check_create_permissions(auth_token, e)
        return e

# vim:tabstop=4 shiftwidth=4 expandtab
