from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ForumTopicManager(ObjectManager):
    """
    Manage Topics in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'closed' : 'get_general',
            'forum' : 'get_foreign_key',
            'name' : 'get_general',
            'posts' : 'get_many_to_many',
            'sticky' : 'get_general',
        })
        self.setters.update({
            'closed' : 'set_general',
            'forum' : 'set_foreign_key',
            'name' : 'set_general',
            'sticky' : 'set_general',
        })
        self.my_django_model = facade.models.ForumTopic
        self.setter = facade.subsystems.Setter

    @service_method
    def create(self, auth_token, name, forum, optional_attributes=None):
        """
        Create a new Topic

        @param name                 name of the Topic
        @type  name                 string
        @param forum                forum FK
        @type  forum                int
        @return                     a reference to the newly created Topic
        """
        if optional_attributes is None:
            optional_attributes = dict()

        new_topic = self.my_django_model(name = name)
        new_topic.blame = facade.managers.BlameManager().create(auth_token)
        new_topic.forum = self._find_by_id(forum, facade.models.Forum)
        for attr in ['sticky', 'closed']:
            if attr in optional_attributes:
                setattr(new_topic, attr, optional_attributes[attr])

        new_topic.save()

        self.authorizer.check_create_permissions(auth_token, new_topic)
        return new_topic

# vim:tabstop=4 shiftwidth=4 expandtab
