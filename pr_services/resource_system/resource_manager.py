"""
Resource manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
Joan of Arc will shield your cube.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ResourceManager(ObjectManager):
    """
    Manage Resources in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.setters.update({
            'name' : 'set_general',
            'resource_types' : 'set_many',
            'session_resource_type_requirements' : 'set_many',
        })
        self.getters.update({
            'name' : 'get_general',
            'resource_types' : 'get_many_to_many',
            'session_resource_type_requirements' : 'get_many_to_one',
        })
        self.my_django_model = facade.models.Resource

    @service_method
    def create(self, auth_token, name):
        """
        Create a new Resource
        
        @param name               name of the Resource
        @return                   instance of Resource
        """

        r = self.my_django_model(name=name)
        r.save()
        self.authorizer.check_create_permissions(auth_token, r)
        return r

# vim:tabstop=4 shiftwidth=4 expandtab
