"""
Venue manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class VenueManager(ObjectManager):
    """
    Manage Venues in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        #: Dictionary of attribute names and the functions used to get them
        self.getters.update({
            'address' : 'get_address',
            'contact' : 'get_general',
            'events' : 'get_many_to_one',
            'hours_of_operation' : 'get_general',
            'name' : 'get_general',
            'owner' : 'get_foreign_key',
            'phone' : 'get_general',
            'region' : 'get_foreign_key',
            'rooms' : 'get_many_to_one',
        })
        self.setters.update({
            'address' : 'set_address',
            'contact' : 'set_general',
            'events' : 'set_many',
            'hours_of_operation' : 'set_general',
            'name' : 'set_general',
            'owner' : 'set_foreign_key',
            'phone' : 'set_general',
            'region' : 'set_foreign_key',
            'rooms' : 'set_many',
        })
        self.my_django_model = facade.models.Venue

    @service_method
    def create(self, auth_token, name, phone, region, optional_attributes=None):
        """
        Common method for Venue creation
        
        Makes sure that the old address does not get orphaned.
        
        @param auth_token           The actor's authentication token
        @param name                 Name for the Venue
        @param phone                Phone number
        @param region               Foreign Key for a region
        @param optional_attributes  Dictionary of optional arguments
        @return                     a reference to the newly created Venue
        """

        if optional_attributes is None:
            optional_attributes = {}

        r = self._find_by_id(region, facade.models.Region)
        venue_blame = facade.managers.BlameManager().create(auth_token)
        v = self.my_django_model(name=name, phone=phone, region=r, blame=venue_blame)
        v.owner = auth_token.user
        if optional_attributes:
            facade.subsystems.Setter(auth_token, self, v, optional_attributes)
        v.save()
        self.authorizer.check_create_permissions(auth_token, v)
        return v

# vim:tabstop=4 shiftwidth=4 expandtab
