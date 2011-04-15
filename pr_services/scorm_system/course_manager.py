"""
CourseManager class
"""

from pr_services import exceptions
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class CourseManager(ObjectManager):
    """
    Manage Courses in the Power Reg system.
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'name' : 'get_general',
            'scos' : 'get_many_to_one',
        })
        self.setters.update({
            'name' : 'get_general',
            'scos' : 'set_many',
        })
        self.my_django_model = facade.models.Course

    @service_method
    def create(self, auth_token):
        """
        Courses cannot be created using this method, but rather are created by using the upload target for SCORM courses.  This manager
        is used to then update the information pertaining to the course.
        """
        raise exceptions.OperationNotPermittedException('Courses cannot be created using the course manager.  Please use the SCORM upload target')

# vim:tabstop=4 shiftwidth=4 expandtab
