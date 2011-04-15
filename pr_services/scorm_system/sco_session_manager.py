"""
ScoSessionManager class

@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.credential_system.assignment_attempt_manager import AssignmentAttemptManager
from pr_services.exceptions import OperationNotPermittedException
from pr_services.rpc.service import service_method
import facade

from datetime import datetime

class ScoSessionManager(AssignmentAttemptManager):
    """
    Manage ScoSessions in the Power Reg system.
    """

    def __init__(self):
        """ constructor """

        super(ScoSessionManager, self).__init__()
        self.getters.update({
            'cmi_core_lesson_location' : 'get_general',
            'cmi_core_lesson_status' : 'get_general',
            'cmi_core_score_max' : 'get_general',
            'cmi_core_score_min' : 'get_general',
            'shared_object' : 'get_general',
            'sco' : 'get_foreign_key',
        })
        self.setters.update({
        })
        self.my_django_model = facade.models.ScoSession

    @service_method
    def create(self, auth_token, assignment):
        """
        Create a ScoSession

        :param assignment:  foreign key for an Assignment
        :type assignment:   int
        """

        assignment_object = self._find_by_id(assignment, facade.models.Assignment)
        ret = self.my_django_model(assignment=assignment_object)
        ret.save()
        self.authorizer.check_create_permissions(auth_token, ret)

        return ret

# vim:tabstop=4 shiftwidth=4 expandtab
