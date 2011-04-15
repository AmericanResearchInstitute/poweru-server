"""
achievement manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class AchievementManager(ObjectManager):
    """
    Manage achievements in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'component_achievements' : 'get_many_to_many',
            'description' : 'get_general',
            'name' : 'get_general',
            'users' : 'get_many_to_many',
            'yielded_achievements' : 'get_many_to_many',
        })
        self.setters.update({
            'component_achievements' : 'set_many',
            'description' : 'set_general',
            'name' : 'set_general',
            'users' : 'set_many',
            'yielded_achievements' : 'set_many',
        })
        self.my_django_model = facade.models.Achievement

    @service_method
    def create(self, auth_token, name, description, component_achievements=None):
        """
        Create a new achievement
        
        @param name                     human-readable name
        @param description              human-readable description
        @param component_achievements   optional list of achievement PKs.  If
                                        the user obtains all of these, they will
                                        be awarded this achievement.
        @return                         a reference to the newly created achievement
        """

        if component_achievements is None:
            component_achievements = []

        achievement = self.my_django_model.objects.create(name=name, description=description)

        for achievement_id in component_achievements:
            component_achievement = self._find_by_id(achievement_id)
            achievement.component_achievements.add(component_achievement)

        self.authorizer.check_create_permissions(auth_token, achievement)
        return achievement

# vim:tabstop=4 shiftwidth=4 expandtab
