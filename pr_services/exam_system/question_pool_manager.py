"""
Question Pool Manager class.

:author: Chris Church <cchurch@americanri.com>
:copyright: Copyright 2010 American Research Institute, Inc.
Where questions go swimming.  Don't pee in the pool.
"""

__docformat__ = "restructuredtext en"

# PowerReg
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class QuestionPoolManager(ObjectManager):
    """
    Manage question pools in the Power Reg system.

    **Attributes:**
     * *exam* -- Reference to the exam containing this question pool.
     * *name* -- Unique name for this question pool within the exam.
     * *order* -- Order of this question pool within the exam.
     * *questions* -- List of foreign keys for question objects.
     * *title* -- Title of this section of the exam.
    """

    def __init__(self):
        """Constructor."""

        super(QuestionPoolManager, self).__init__()
        self.getters.update({
            'exam': 'get_foreign_key',
            'name': 'get_general',
            'order': 'get_general',
            'questions': 'get_many_to_one',
            'number_to_answer' : 'get_general',
            'randomize_questions' : 'get_general',
            'title': 'get_general',
        })
        self.setters.update({
            'exam': 'set_foreign_key',
            'name': 'set_general',
            'order': 'set_general',
            'questions': 'set_many',
            'number_to_answer' : 'set_general',
            'randomize_questions' : 'set_general',
            'title': 'set_general',
        })
        self.my_django_model = facade.models.QuestionPool

    @service_method
    def create(self, auth_token, exam_id, title, optional_parameters=None):
        """
        Create a new question pool.
        
        :param auth_token:          The authentication token of the acting user
        :type auth_token:           pr_services.models.AuthToken
        :param exam_id:             Reference to the exam containing this
                                    question pool.
        :type exam_id:              int
        :param title:               Title of this section of the exam.
        :type title:                unicode
        :param optional_parameters: optional parameters, possibly including:

            * name
            * order
            * questions

        :type optional_parameters:  dict or None
        :return:                    Reference to the newly created question pool.
        """

        if optional_parameters is None:
            optional_parameters = {}

        exam = self._find_by_id(exam_id, facade.models.Exam)

        qp = self.my_django_model(exam=exam, title=title)
        qp.save()
        if optional_parameters:
            facade.subsystems.Setter(auth_token, self, qp, optional_parameters)
            qp.save()
        self.authorizer.check_create_permissions(auth_token, qp)
        return qp

# vim:tabstop=4 shiftwidth=4 expandtab
