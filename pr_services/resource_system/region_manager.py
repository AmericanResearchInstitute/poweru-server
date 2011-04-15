"""
Region manager class

@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services import exceptions
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class RegionManager(ObjectManager):
    """
    Manage Regions in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.setters.update({
            'name' : 'set_general',
            'events' : 'set_many',
            'venues' : 'set_many',
        })
        self.getters.update({
            'name' : 'get_general',
            'events' : 'get_many_to_one',
            'venues' : 'get_many_to_one',
        })
        self.my_django_model = facade.models.Region

    @service_method
    def create(self, auth_token, name, optional_attributes=None):
        """
        Create a new Region
        
        @param name                name of the Region
        @return                    a reference to the newly created Region
        """

        r = self.my_django_model(name=name)
        if optional_attributes:
            facade.subsystems.Setter(auth_token, self, r, optional_attributes)
        r.save()
        self.authorizer.check_create_permissions(auth_token, r)
        return r

# vim:tabstop=4 shiftwidth=4 expandtab
