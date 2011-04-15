"""
SessionTemplateUserRoleRequirement manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class SessionTemplateUserRoleRequirementManager(ObjectManager):
    """
    Manage SessionTemplateUserRoleRequirements in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'session_template' : 'get_foreign_key',
            'session_user_role' : 'get_foreign_key',
            'max' : 'get_general',
            'min' : 'get_general',
        })
        self.setters.update({
            'session_template' : 'set_foreign_key',
            'session_user_role' : 'set_foreign_key',
            'max' : 'set_general',
            'min' : 'set_general',
        })
        self.my_django_model = facade.models.SessionTemplateUserRoleReq

    @service_method
    def create(self, auth_token, session_template_id, session_user_role_id, min, max,
        credential_type_ids=None):
        
        """
        Create a new SessionTemplateUserRoleRequirement
        
        @param session_template_id  Primary key for an session_template
        @param session_user_role_id Primary key for a session_user_role
        @param min                  Minimum number required
        @param max                  Maximum number allowed
        @param credential_type_ids  Array of credential_type primary keys
        @return                     A reference to the newly created SessionTemplateUserRoleRequirement
        """

        if credential_type_ids is None:
            credential_type_ids = []

        session_template_instance = self._find_by_id(session_template_id, facade.models.SessionTemplate)
        sur_instance = self._find_by_id(session_user_role_id, facade.models.SessionUserRole)
        c = self.my_django_model(session_template=session_template_instance, session_user_role=sur_instance,
                min=min, max=max)
        c.save() # We must save so that we can get a primary key, and thus establish
        # many-to-many relationships below
        if credential_type_ids:
            facade.subsystems.Setter(auth_token, self, c, {'credential_types' : {'add' : credential_type_ids}})
        self.authorizer.check_create_permissions(auth_token, c)
        return c

# vim:tabstop=4 shiftwidth=4 expandtab
