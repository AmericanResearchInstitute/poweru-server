from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ForumPostManager(ObjectManager):
    """
    Manage Posts in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'topic' : 'get_foreign_key',
            'body' : 'get_general',
            'attachments' : 'get_many_to_many',
        })
        self.setters.update({
            'topic' : 'set_foreign_key',
            'body' : 'set_general',
        })
        self.my_django_model = facade.models.ForumPost
        self.setter = facade.subsystems.Setter

    @service_method
    def create(self, auth_token, body, topic, optional_attributes=None):
        """
        Create a new Post

        @param body                 body of the Post
        @type  body                 string
        @param topic                topic FK
        @type  topic                int
        @return                     a reference to the newly created Post
        """
        if optional_attributes is None:
            optional_attributes = dict()

        new_post = self.my_django_model(user=auth_token.user, body=body)
        new_post.blame = facade.managers.BlameManager().create(auth_token)
        new_post.topic = self._find_by_id(topic, facade.models.ForumTopic)

        new_post.save()

        self.authorizer.check_create_permissions(auth_token, new_post)
        return new_post

# vim:tabstop=4 shiftwidth=4 expandtab
