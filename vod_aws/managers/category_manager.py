"""
CategoryManager class

:copyright: Copyright 2009 American Research Institute, Inc.
"""

__docformat__ = "restructuredtext en"

import facade
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
from pr_services.utils import Utils

class CategoryManager(ObjectManager):
    """Manage Categories in the Power Reg system"""

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'approved_videos' : 'get_general',
            'authorized_groups' : 'get_many_to_many',
            'managers' : 'get_many_to_many',
            'name' : 'get_general',
            'locked' : 'get_general',
            'videos' : 'get_many_to_many',
        })
        self.setters.update({
            'authorized_groups' : 'set_many',
            'managers' : 'set_many',
            'name' : 'set_general',
            'locked' : 'set_general',
            'videos' : 'set_many',
        })
        self.my_django_model = facade.models.Category

    @service_method
    def create(self, auth_token, name):
        """
        Create a Category.

        :param auth_token:          The authentication token of the acting user
        :type auth_token:           models.AuthToken
        :param name:                The name of the category to be created.
        :type name:                 string
        :return:                    The new Category instance
        """
        new_category = self.my_django_model.objects.create(name=name)
        self.authorizer.check_create_permissions(auth_token, new_category)
        return new_category

    @service_method
    def admin_categories_view(self, auth_token):
        categories = self.get_filtered(auth_token, {}, ['name', 'managers', 'authorized_groups', 'locked'])

        categories = Utils.merge_queries(categories, facade.managers.GroupManager(), auth_token,
            ['name'], 'authorized_groups')

        return Utils.merge_queries(categories, facade.managers.UserManager(), auth_token, 
            ['last_name', 'first_name', 'email'], 'managers')


# vim:tabstop=4 shiftwidth=4 expandtab
