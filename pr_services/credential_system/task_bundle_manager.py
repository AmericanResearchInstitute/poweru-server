"""
TaskBundleManager class

:copyright: Copyright 2010 American Research Institute, Inc.
How many licks does it take to get to the center?  The world may never know.
"""
__docformat__ = "restructuredtext en"

from pr_services import exceptions
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class TaskBundleManager(ObjectManager):
    """
    Manage Task Bundles in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        super(TaskBundleManager, self).__init__()
        self.getters.update({
            'name' : 'get_general',
            'description' : 'get_general',
            'tasks' : 'get_tasks_from_task_bundle',
        })
        self.setters.update({
            'name' : 'set_general',
            'description' : 'set_general',
            'tasks' : 'set_tasks_for_task_bundle',
        })
        self.my_django_model = facade.models.TaskBundle

    @service_method
    def create(self, auth_token, name, description, tasks):
        """
        Creates a new task bundle

        :param name:            user-visible name of the task bundle
        :type name:             string
        :param description:     description of the task bundle
        :type description:      string
        :param tasks:           list of dictionaries, each with key "id" for the
                                Task FK. Optionally include key "presentation_order"
                                and/or key "continue_automatically"
        :type tasks:            list

        :returns: a reference to the newly created task bundle
        """
        
        task_bundle = self.my_django_model.objects.create(name=name,
            description=description)

        for task in tasks:
            tbta = facade.models.TaskBundleTaskAssociation(task_bundle=task_bundle)
            tbta.task = self._find_by_id(task['id'], facade.models.Task)
            for attr_name in ['presentation_order', 'continue_automatically']:
                if attr_name in task:
                    setattr(tbta, attr_name, task[attr_name])
            tbta.save()

        self.authorizer.check_create_permissions(auth_token, task_bundle)
        
        return task_bundle

# vim:tabstop=4 shiftwidth=4 expandtab
