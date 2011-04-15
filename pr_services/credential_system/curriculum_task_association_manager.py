"""
curriculum_task_association manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class CurriculumTaskAssociationManager(ObjectManager):
    """
    Manage curriculum_task_associations in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'continue_automatically' : 'get_general',
            'curriculum' : 'get_foreign_key',
            'days_before_start' : 'get_general',
            'days_to_complete' : 'get_general',
            'presentation_order' : 'get_general',
            'task' : 'get_foreign_key',
            'task_bundle' : 'get_foreign_key',
        })
        self.setters.update({
            'continue_automatically' : 'set_general',
            'curriculum' : 'set_foreign_key',
            'days_before_start' : 'set_general',
            'days_to_complete' : 'set_general',
            'presentation_order' : 'set_general',
            'task' : 'set_foreign_key',
            'task_bundle' : 'set_foreign_key',
        })
        self.my_django_model = facade.models.CurriculumTaskAssociation

    @service_method
    def bulk_create(self, auth_token, parameter_sets):
        ret = []
        for ps in parameter_sets:
            ret.append(self.create(auth_token, **ps).id)
        return ret

    @service_method
    def create(self, auth_token, curriculum, task, optional_attributes = None):
        """
        Create a new curriculum_task_association.
        
        :param  curriculum:         FK for a curriculum
        :param  task:               FK for a task
        :param  optional_attributes:dict of optional attributes including
                                    'presentation_order', 'days_before_start',
                                    'continue_automatically', 'task_bundle'
        :return:                    a reference to the newly created curriculum_task_association
        """

        if optional_attributes is None:
            optional_attributes = {}

        c = self.my_django_model()
        c.curriculum = self._find_by_id(curriculum, facade.models.Curriculum)
        c.task = self._find_by_id(task, facade.models.Task)
        if 'task_bundle' in optional_attributes:
            c.task_bundle = self._find_by_id(optional_attributes['task_bundle'], facade.models.TaskBundle)
        for attribute in ['presentation_order', 'continue_automatically', 'days_before_start', 'days_to_complete']:
            if attribute in optional_attributes:
                setattr(c, attribute, optional_attributes[attribute])
        c.save()
        self.authorizer.check_create_permissions(auth_token, c)
        return c

# vim:tabstop=4 shiftwidth=4 expandtab
