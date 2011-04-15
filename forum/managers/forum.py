from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ForumManager(ObjectManager):
    """
    Manage Forums in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'category' : 'get_many_to_many',
            'description' : 'get_general',
            'name' : 'get_general',
            'topics' : 'get_many_to_many',
        })
        self.setters.update({
            'category' : 'set_many',
            'description' : 'set_general',
            'name' : 'set_general',
        })
        self.my_django_model = facade.models.Forum
        self.setter = facade.subsystems.Setter

    @service_method
    def create(self, auth_token, name, categories, optional_attributes=None):
        """
        Create a new Forum

        @param name                 name of the Forum
        @type  name                 string
        @param categories           list of category FKs
        @type  categories           list
        @return                     a reference to the newly created Forum
        """
        if optional_attributes is None:
            optional_attributes = dict()

        new_forum = self.my_django_model(name = name)
        new_forum.blame = facade.managers.BlameManager().create(auth_token)
        if 'description' in optional_attributes:
            new_forum.description = optional_attributes['description']

        new_forum.save()

        new_forum.categories.add(*categories)

        self.authorizer.check_create_permissions(auth_token, new_forum)
        return new_forum

# vim:tabstop=4 shiftwidth=4 expandtab
