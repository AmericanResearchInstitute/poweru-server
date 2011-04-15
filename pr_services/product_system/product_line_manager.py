"""
ProductLine manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ProductLineManager(ObjectManager):
    """
    Manage ProductLines in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'instructor_managers' : 'get_many_to_many',
            'instructors' : 'get_many_to_many',
            'managers' : 'get_many_to_many',
            'name' : 'get_general',
        })
        self.setters.update({
            'instructor_managers' : 'set_many',
            'instructors' : 'set_many',
            'managers' : 'set_many',
            'name' : 'set_general',
        })
        self.my_django_model = facade.models.ProductLine

    @service_method
    def create(self, auth_token, name):
        """
        Create a new ProductLine
        
        @param name                name of the ProductLine
        @return                    a reference to the newly created ProductLine
        """

        c = self.my_django_model(name=name)
        c.save()
        self.authorizer.check_create_permissions(auth_token, c)
        return c

# vim:tabstop=4 shiftwidth=4 expandtab
