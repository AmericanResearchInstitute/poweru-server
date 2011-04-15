from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ForumCategoryManager(ObjectManager):
    """
    Manage Categorys in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'name' : 'get_general',
            'forums' : 'get_many_to_many',
        })
        self.setters.update({
            'name' : 'set_general',
        })
        self.my_django_model = facade.models.ForumCategory
        self.setter = facade.subsystems.Setter

    @service_method
    def create(self, auth_token, name, optional_attributes=None):
        """
        Create a new Category

        @param name                name of the Category
        @return                    a reference to the newly created Category
        """
        if optional_attributes is None:
            optional_attributes = dict()

        blame = facade.managers.BlameManager().create(auth_token)

        new_category = self.my_django_model.objects.create(name=name, blame=blame)

        self.setter(auth_token, self, new_category, optional_attributes)

        self.authorizer.check_create_permissions(auth_token, new_category)
        return new_category

# vim:tabstop=4 shiftwidth=4 expandtab
