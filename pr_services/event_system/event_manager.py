"""
Event manager class
"""

from datetime import datetime, timedelta
from pr_services import pr_time
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade
import settings

class EventManager(ObjectManager):
    """
    Manage Events in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.setters.update({
            'name' : 'set_general',
            'region' : 'set_foreign_key',
            'event_template' : 'set_foreign_key',
            'title' : 'set_general',
            'description' : 'set_general',
            'organization' : 'set_foreign_key',
            'owner' : 'set_foreign_key',
            'lag_time' : 'set_general',
            'lead_time' : 'set_general',
            'start' : 'set_time',
            'end' : 'set_time',
            'venue' : 'set_foreign_key',
            'product_line' : 'set_foreign_key',
            'notify_cfgs' : 'set_many',
            'external_reference' : 'set_general',
            'url' : 'set_general',
            'facebook_message' : 'set_general',
            'twitter_message' : 'set_general',
        })
        self.getters.update({
            'event_template' : 'get_foreign_key',
            'organization' : 'get_foreign_key',
            'name' : 'get_general',
            'region' : 'get_foreign_key',
            'title' : 'get_general',
            'description' : 'get_general',
            'owner' : 'get_foreign_key',
            'lag_time' : 'get_general',
            'lead_time' : 'get_general',
            'start' : 'get_time',
            'end' : 'get_time',
            'sessions' : 'get_many_to_one',
            'notify_cfgs' : 'get_many_to_one',
            'venue' : 'get_foreign_key',
            'product_line' : 'get_foreign_key',
            'external_reference' : 'get_general',
            'status' : 'get_status_from_event',
            'url' : 'get_general',
            'facebook_message' : 'get_general',
            'twitter_message' : 'get_general',
        })
        self.my_django_model = facade.models.Event

    @service_method
    def create(self, auth_token, name_prefix, title, description, start, end, organization, product_line,
            optional_attributes=None):
        
        """
        Create a new Event.
        
        A region or a venue must be provided.
        
        @param name_prefix          prefix for the human-readable unique identifier 'name'
        @param title                title of the Event
        @param description          description of the Event
        @param start                Date on which the Event starts, as an ISO8601 string.
                                    If you provide hour, minute, or second, they will be ignored.
        @param end                  Date on which the Event ends, as an ISO8601 string.
                                    If you provide hour, minute, or second, they will be ignored.
        @param organization         FK for organization
        @param product_line         Foreign Key for a product_line
        @param optional_attributes  currently only 'venue', 'region', 'event_template', and 'lead_time'
        @return                     a reference to the newly created Event
        """
        
        if optional_attributes is None:
            optional_attributes = {}
        
        start_date = pr_time.iso8601_to_datetime(start).replace(microsecond=0, second=0,
            minute=0, hour=0)
        end_date = pr_time.iso8601_to_datetime(end).replace(microsecond=0, second=0,
            minute=0, hour=0)
        e = self.my_django_model.objects.create(title=title, description=description,
                start=start_date,
                organization = self._find_by_id(organization, facade.models.Organization),
                product_line = self._find_by_id(product_line, facade.models.ProductLine),
                end = end_date,
                owner = auth_token.user)
        e.name = '%s%d' % (name_prefix if name_prefix is not None else '', e.id)
        if 'lag_time' not in optional_attributes:
            optional_attributes['lag_time'] = settings.DEFAULT_EVENT_LAG_TIME
        facade.subsystems.Setter(auth_token, self, e, optional_attributes)
        e.save()
        
        self.authorizer.check_create_permissions(auth_token, e)
        return e

# vim:tabstop=4 shiftwidth=4 expandtab
