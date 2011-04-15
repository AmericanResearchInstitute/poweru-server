"""
ResourceType manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ResourceTypeManager(ObjectManager):
    """
    Manage ResourceTypes in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.setters.update({
            'name' : 'set_general',
            'resources' : 'set_many',
            'sessiontemplateresourcetypereqs' : 'set_many',
            'sessionresourcetyperequirements' : 'set_many',
        })
        self.getters.update({
            'name' : 'get_general',
            'resources' : 'get_many_to_many',
            'sessionresourcetyperequirements' : 'get_many_to_one',
            'sessiontemplateresourcetypereqs' : 'get_many_to_one',
        })
        self.my_django_model = facade.models.ResourceType

    @service_method
    def create(self, auth_token, name):
        """
        Create a new ResourceType
        
        @param name               name of the ResourceType
        @return                   isntance of ResourceType
        """

        r = self.my_django_model(name=name)
        r.save()
        self.authorizer.check_create_permissions(auth_token, r)
        return r

# vim:tabstop=4 shiftwidth=4 expandtab
