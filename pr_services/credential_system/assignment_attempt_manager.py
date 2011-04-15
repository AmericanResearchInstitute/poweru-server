"""
AssignmentAttemptManager class

@copyright Copyright 2010 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
import facade

class AssignmentAttemptManager(ObjectManager):
    """
    Manage AssignmentAttempts in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'assignment' : 'get_foreign_key',
            'date_completed' : 'get_time',
            'date_started' : 'get_time',
        })
        self.setters.update({
            'date_completed' : 'set_time',
            'date_started' : 'set_time',
        })
        self.my_django_model = facade.models.AssignmentAttempt
        self.subclass_manager_map = {
            'exam' : {'manager' : 'ExamSessionManager',
                      'kwargs' : {'fetch_all':False, 'resume':False}},
            'sco' : {'manager' : 'ScoSessionManager',},
            'video' : {'manager' : 'VideoSessionManager'},
        }

    def _create(self, auth_token, assignment):
        """
        create the appropriate subtype of AssignmentAttempt

        :param assignment:  instance of an assignment
        :type assignment:   facade.models.Assignment

        :return:            whatever the sub-class's manager returns
        """

        task = assignment.task.downcast_completely()
        if task.final_type.model in self.subclass_manager_map:
            self.logger.debug('type = %s' % (task.final_type.model))
            manager_info = self.subclass_manager_map[task.final_type.model]
            return getattr(facade.managers, manager_info['manager'])().create(auth_token, assignment.id,
                **manager_info.get('kwargs', {}))

# vim:tabstop=4 shiftwidth=4 expandtab
