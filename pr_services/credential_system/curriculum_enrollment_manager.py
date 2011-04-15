"""
curriculum_enrollment manager class

@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade
from pr_services import pr_time

class CurriculumEnrollmentManager(ObjectManager):
    """
    Manage curriculum_enrollments in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'assignments' : 'get_many_to_one',
            'curriculum' : 'get_foreign_key',
            'users' : 'get_many_to_many',
            'start' : 'get_time',
            'end' : 'get_time',
            'user_completion_statuses' : 'get_general',
        })
        self.setters.update({
            'curriculum' : 'set_foreign_key',
            'users' : 'set_many',
            'start' : 'set_time',
            'end' : 'set_time',
        })
        self.my_django_model = facade.models.CurriculumEnrollment

    @service_method
    def create(self, auth_token, curriculum, start, end, users=None):
        """
        Create a new curriculum_enrollment.
        
        :param  curriculum:     FK for a curriculum
        :param  start:          start date in ISO8601 format
        :param  end:            end date in ISO8601 format
        :return:                a reference to the newly created curriculum_enrollment
        """

        start_date = pr_time.iso8601_to_datetime(start).replace(microsecond=0, second=0,
            minute=0, hour=0)
        end_date = pr_time.iso8601_to_datetime(end).replace(microsecond=0, second=0,
            minute=0, hour=0)

        c = self.my_django_model(start=start_date, end=end_date)
        c.curriculum = self._find_by_id(curriculum, facade.models.Curriculum)
        c.save()
        if users is not None:
            for user in facade.models.User.objects.filter(id__in=users):
                facade.models.CurriculumEnrollmentUserAssociation.objects.create(user=user, curriculum_enrollment=c)
        self.authorizer.check_create_permissions(auth_token, c)
        return c

# vim:tabstop=4 shiftwidth=4 expandtab
