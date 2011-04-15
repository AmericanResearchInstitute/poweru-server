"""
SessionTemplate manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class SessionTemplateManager(ObjectManager):
    """
    Manage SessionTemplates in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        #: Dictionary of attribute names and the functions used to get them
        self.getters.update({
            'active' : 'get_general',
            'audience' : 'get_general',
            'session_template_resource_type_requirements' : 'get_many_to_one',
            'session_template_user_role_requirements' : 'get_many_to_one',
            'description' : 'get_general',
            'duration' : 'get_general',
            'event_template' : 'get_foreign_key',
            'sessions' : 'get_many_to_one',
            'fullname' : 'get_general',
            'lead_time' : 'get_general',
            'modality' : 'get_general',
            'price' : 'get_general',
            'product_line' : 'get_foreign_key',
            'sequence' : 'get_general',
            'shortname' : 'get_general',
            'version' : 'get_general',
        })
        #: Dictionary of attribute names and the functions used to set them
        self.setters.update({
            'active' : 'set_general',
            'event_template' : 'set_foreign_key',
            'session_template_resource_type_requirements' : 'set_many',
            'session_template_user_role_requirements' : 'set_many',
            'product_line' : 'set_foreign_key',
            'fullname' : 'set_general',
            'sessions' : 'set_many',
            'shortname' : 'set_general',
            'version' : 'set_general',
            'description' : 'set_general',
            'audience' : 'set_general',
            'price' : 'set_general',
            'lead_time' : 'set_general',
            'sequence' : 'set_general',
            'duration' : 'set_general',
            'modality' : 'set_general',
        })
        self.my_django_model = facade.models.SessionTemplate

    @service_method
    def create(self, auth_token, shortname, fullname, version, description, price,
            lead_time, active, modality='Generic', optional_attributes=None):
        """
        Create a SessionTemplate
        
        @param shortname              A short name, which must be unique
        @param fullname               Full name
        @param version                Version
        @param description            description of the SessionTemplate
        @param price                  price of the SessionTemplate in US cents
        @param lead_time              lead time for the SessionTemplate in seconds
        @param active                 Bool, active or not
        @param modality               Type of SessionTemplate
        @param optional_attributes    dictionary of optional attribute values indexed by name
        @return                       Instance of SessionTemplate
        """

        if optional_attributes is None:
            optional_attributes = {}

        new_session_template = self._create(auth_token, shortname, fullname, version, description,
                price, lead_time, active, modality, optional_attributes)
        self.authorizer.check_create_permissions(auth_token, new_session_template)
        return new_session_template

    def _create(self, auth_token, shortname, fullname, version, description, price,
            lead_time, active, modality = 'Generic', optional_attributes=None):
        """
        Create a SessionTemplate
        
        @param shortname              A short name, which must be unique
        @param fullname               Full name
        @param version                Version
        @param description            description of the SessionTemplate
        @param price                  price of the SessionTemplate in US cents
        @param lead_time              lead time for the SessionTemplate in seconds
        @param active                 Bool, active or not
        @param optional_attributes    dictionary of optional attribute values indexed by name
        @return                       Instance of SessionTemplate
        """

        if optional_attributes is None:
            optional_attributes = {}

        c = self.my_django_model(shortname = shortname, fullname = fullname, version = version,
                description = description, price = price, lead_time = lead_time,
                active = active, modality = modality)
        if 'product_line' in optional_attributes:
            the_product_line = self._find_by_id(optional_attributes['product_line'], facade.models.ProductLine)
            c.product_line = the_product_line
            del optional_attributes['product_line']
        c.save()
        if optional_attributes:
            facade.subsystems.Setter(auth_token, self, c, optional_attributes)
            c.save()
        return c

    def _delete(self, auth_token, session_template_id):
        """
        delete a SessionTemplate
        
        @param auth_token           the auth_token of someone authorized to create/update SessionTemplates
        @param session_template_id  the id of the SessionTemplate to be deleted
        """

        session_template = self._find_by_id(session_template_id)
        self.authorizer.check_delete_permissions(auth_token, session_template)
        session_template.active = False
        session_template.save()

# vim:tabstop=4 shiftwidth=4 expandtab
