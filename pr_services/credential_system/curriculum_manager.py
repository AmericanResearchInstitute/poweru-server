"""
curriculum manager class

@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class CurriculumManager(ObjectManager):
    """
    Manage curriculums in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'achievements' : 'get_many_to_many',
            'name' : 'get_general',
            'organization' : 'get_foreign_key',
            'tasks' : 'get_many_to_many',
        })
        self.setters.update({
            'achievements' : 'set_many',
            'name' : 'set_general',
            'organization' : 'set_foreign_key',
            'tasks' : 'set_many',
        })
        self.my_django_model = facade.models.Curriculum

    @service_method
    def create(self, auth_token, name, organization=None):
        """
        Create a new curriculum.
        
        :param  name:           human-readable name
        :param  organization:   organization to which this belongs
        :return:                a reference to the newly created curriculum
        """

        c = self.my_django_model(name=name)
        if organization is not None:
            c.organization = self._find_by_id(organization, facade.models.Organization)
        c.save()
        self.authorizer.check_create_permissions(auth_token, c)
        return c

# vim:tabstop=4 shiftwidth=4 expandtab
