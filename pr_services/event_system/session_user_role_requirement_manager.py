"""
SessionUserRoleRequirement manager class
"""

from datetime import datetime
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade
import logging

class SessionUserRoleRequirementManager(facade.managers.TaskManager):
    """
    Manage SessionUserRoleRequirements in the Power Reg system
    """
    
    def __init__(self):
        """ constructor """

        super(SessionUserRoleRequirementManager, self).__init__()
        self.getters.update({
            'credential_types' : 'get_many_to_many',
            'session' : 'get_foreign_key',
            'session_user_role' : 'get_foreign_key',
            'max' : 'get_general',
            'min' : 'get_general',
            'ignore_room_capacity' : 'get_general',
        })
        self.setters.update({
            'credential_types' : 'set_many',
            'session' : 'set_foreign_key',
            'session_user_role' : 'set_foreign_key',
            'max' : 'set_general',
            'min' : 'set_general',
            'ignore_room_capacity' : 'set_general',
        })
        self.my_django_model = facade.models.SessionUserRoleRequirement

    @service_method
    def create(self, auth_token, session_id, session_user_role_id, min, max,
        unused, credential_type_ids=None, optional_attributes=None):
        
        """
        Create a new SessionUserRoleRequirement
        
        @param session_id               Primary key for an session
        @param session_user_role_id     Primary key for an session_user_role
        @param min                      Minimum number required
        @param max                      Maximum number allowed
        @param unused                   bool: obsolete positional parameter retained for compatibility
        @param credential_type_ids      Array of credential_type primary keys
        @return                         A reference to the newly created SessionUserRoleRequirement
        """

        if credential_type_ids is None:
            credential_type_ids = []

        session = self._find_by_id(session_id, facade.models.Session)
        session_user_role = self._find_by_id(session_user_role_id, facade.models.SessionUserRole)
        new_surr = self.my_django_model(session=session, session_user_role=session_user_role, min=min, max=max)
        new_surr.save()
        if credential_type_ids:
            facade.subsystems.Setter(auth_token, self, new_surr,
                    {'credential_types' : {'add' : credential_type_ids}})
        new_surr.save()

        if optional_attributes is not None:
            self._set_optional_attributes(new_surr, optional_attributes)
            new_surr.save()
        self.authorizer.check_create_permissions(auth_token, new_surr)
        return new_surr

# vim:tabstop=4 shiftwidth=4 expandtab
