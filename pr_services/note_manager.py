"""
Note manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
I'll disconnect the telephone.
"""

from object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class NoteManager(ObjectManager):
    """
    Manage Notes in the Power Reg system.

    Notes are created here and then associated with
    objects by modifying their 'notes' attributes.
    """

    def __init__(self):
        """ constructor """
        ObjectManager.__init__(self)
        self.getters.update({
            'text' : 'get_general',
        })
        self.setters.update({
            'text' : 'set_general',
        })
        # We don't allow Notes about Notes, but it would be a lot funnier if we did
        if self.getters.has_key('notes'):
            del self.getters['notes']
        if self.getters.has_key('notes'):
            del self.setters['notes']
        
        self.my_django_model = facade.models.Note

    @service_method
    def create(self, auth_token, text):
        """
        Create a new Note.  After creating a note, be sure to associate it with
        the object(s) it pertains to.
        
        @param auth_token   The authentication token of the acting user
        @type auth_token    unicode
        @param text         The Note text
        @type text          unicode
        @return             The primary key of the new Note
        @rtype              models.Note (as dict)
        """
        n = self.my_django_model(text=text)
        n.save()
        self.authorizer.check_create_permissions(auth_token, n)
        return n

# vim:tabstop=4 shiftwidth=4 expandtab
