"""
EventTemplate manager class
"""

from datetime import datetime, timedelta
from pr_services import pr_time
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade
import settings

class EventTemplateManager(ObjectManager):
    """
    Manage EventTemplates in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.setters.update({
            'description' : 'set_general',
            'external_reference' : 'set_general',
            'facebook_message' : 'set_general',
            'lag_time' : 'set_general',
            'lead_time' : 'set_general',
            'name_prefix' : 'set_general',
            'notify_cfgs' : 'set_many',
            'organization' : 'set_foreign_key',
            'product_line' : 'set_foreign_key',
            'title' : 'set_general',
            'twitter_message' : 'set_general',
            'url' : 'set_general',
        })
        self.getters.update({
            'description' : 'get_general',
            'external_reference' : 'get_general',
            'facebook_message' : 'get_general',
            'lag_time' : 'get_general',
            'lead_time' : 'get_general',
            'name_prefix' : 'get_general',
            'notify_cfgs' : 'get_many_to_one',
            'organization' : 'get_foreign_key',
            'product_line' : 'get_foreign_key',
            'session_templates' : 'get_many_to_one',
            'title' : 'get_general',
            'twitter_message' : 'get_general',
            'url' : 'get_general',
            'events' : 'get_many_to_one',
        })
        self.my_django_model = facade.models.EventTemplate

    @service_method
    def create(self, auth_token, name_prefix, title, description, optional_attributes=None):
        
        """
        Create a new EventTemplate.
        
        @param name_prefix          Prefix that will be used in generating a unique name
        @param title                title of the EventTemplate
        @param description          description of the EventTemplate
        @param optional_attributes  'external_reference', facebook_template, lag_time, lead_time,
                                    organization, product_line, twitter_template, url
        @return                     a reference to the newly created EventTemplate
        """
        
        if optional_attributes is None:
            optional_attributes = {}
        
        e = self.my_django_model.objects.create(name_prefix=name_prefix, title=title, description=description)
        if 'lag_time' not in optional_attributes:
            optional_attributes['lag_time'] = settings.DEFAULT_EVENT_LAG_TIME
        facade.subsystems.Setter(auth_token, self, e, optional_attributes)
        e.save()
        
        self.authorizer.check_create_permissions(auth_token, e)
        return e

# vim:tabstop=4 shiftwidth=4 expandtab
