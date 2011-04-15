"""
Group manager class

@author Michael Hrivank <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
from pr_services.utils import Utils
import facade

class GroupManager(ObjectManager):
    """
    Manage Groups in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'categories' : 'get_many_to_many',
            'default' : 'get_general',
            'managers' : 'get_many_to_many',
            'name' : 'get_general',
            'users' : 'get_many_to_many',
        })
        self.setters.update({
            'categories' : 'set_many',
            'default' : 'set_general',
            'managers' : 'set_many',
            'name' : 'set_general',
            'users' : 'set_many',
        })
        self.my_django_model = facade.models.Group
        self.setter = facade.subsystems.Setter

    @service_method
    def create(self, auth_token, name, optional_attributes=None):
        """
        Create a new Group
        
        @param name                name of the Group
        @return                    a reference to the newly created Group
        """
        if optional_attributes is None:
            optional_attributes = dict()

        new_group = self.my_django_model.objects.create(name = name)

        self.setter(auth_token, self, new_group, optional_attributes)

        self.authorizer.check_create_permissions(auth_token, new_group)
        return new_group

    @service_method
    def vod_admin_groups_view(self, auth_token):
        groups = self.get_filtered(auth_token, {}, ['name', 'categories'])

        return Utils.merge_queries(groups, facade.managers.CategoryManager(), auth_token, 
            ['name'], 'categories')

# vim:tabstop=4 shiftwidth=4 expandtab
