from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ForumPostAttachmentManager(ObjectManager):
    """
    Manage Attachments in the Power Reg Forum system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'description' : 'get_general',
            'name' : 'get_general',
            'post' : 'get_foreign_key',
        })
        self.setters.update({
            'description' : 'set_general',
            'name' : 'set_general',
            'post' : 'set_foreign_key',
        })
        self.my_django_model = facade.models.ForumPostAttachment
        self.setter = facade.subsystems.Setter

    @service_method
    def create(self, auth_token, name, post, optional_attributes=None):
        """
        Create a new Attachment

        @param name                 name of the Attachment
        @type  name                 string
        @param post                 post FK
        @type  post                 int
        @return                     a reference to the newly created Attachment
        """
        if optional_attributes is None:
            optional_attributes = dict()

        new_attachment = self.my_django_model(name=name)
        new_attachment.blame = facade.managers.BlameManager().create(auth_token)
        new_attachment.post = self._find_by_id(post, facade.models.ForumPost)

        new_attachment.save()

        self.authorizer.check_create_permissions(auth_token, new_attachment)
        return new_attachment

# vim:tabstop=4 shiftwidth=4 expandtab
