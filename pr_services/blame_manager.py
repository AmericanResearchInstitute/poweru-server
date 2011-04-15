"""
Blame manager class
"""

import object_manager
import exceptions
import facade

class BlameManager(object_manager.ObjectManager):
    """
    Manage Blames in the Power Reg system
    """

    def __init__(self):
        """ contructor """

        object_manager.ObjectManager.__init__(self)
        self.my_django_model = facade.models.Blame

    def create(self, auth_token):
        """
        Create a new Blame
        
        @return                    a reference to the newly created Blame
        """

        if isinstance(auth_token, facade.models.AuthToken):
            return self.my_django_model.objects.create(user=auth_token.user, ip=auth_token.ip)
        else:
            raise exceptions.ObjectNotFoundException('AuthToken')

# vim:tabstop=4 shiftwidth=4 expandtab
