"""
Answer Manager class.

:author: Chris Church <cchurch@americanri.com>
:copyright: Copyright 2010 American Research Institute, Inc.
I have all the answers.  I am the magic 8 ball.
"""

__docformat__ = "restructuredtext en"

# PowerReg
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class AnswerManager(ObjectManager):
    """
    Manage answers in the Power Reg system.

    **Attributes:**
     * *correct* -- True if this answer is a correct one.
     * *end_exam* -- When True and this answer is selected, end the exam after this question pool.
     * *end_question_pool* -- When True and this answer is selected, immediately end the question pool.
     * *label* -- The text presented to the user for this answer.
     * *name* -- Unique name for this answer within the exam.
     * *next_question_pool* -- When set, determines the next question pool when this answer is selected.
     * *order* -- Order of this answer within the list of possible choices.
     * *question* -- Reference to Question to which this answer applies.
     * *responses* -- List of foreign keys for response objects.
     * *text_response* -- When True and this answer is selected, allow an additional text response.
     * *value* -- The actual value for this answer instead of the label.
    """

    def __init__(self):
        """Constructor."""

        super(AnswerManager, self).__init__()
        self.getters.update({
            'correct': 'get_general',
            'end_exam': 'get_general',
            'end_question_pool': 'get_general',
            'label': 'get_general',
            'name': 'get_general',
            'next_question_pool': 'get_foreign_key',
            'order': 'get_general',
            'question': 'get_foreign_key',
            'responses': 'get_many_to_many',
            'text_response': 'get_general',
            'value': 'get_general',
        })
        self.setters.update({
            'correct': 'set_general',
            'end_exam': 'set_general',
            'end_question_pool': 'set_general',
            'label': 'set_general',
            'name': 'set_general',
            'next_question_pool': 'set_foreign_key',
            'order': 'set_general',
            'question': 'set_foreign_key',
            'responses': 'set_many',
            'text_response': 'set_general',
            'value': 'set_general',
        })
        self.my_django_model = facade.models.Answer

    @service_method
    def create(self, auth_token, question_id, label, optional_parameters=None):
        """
        Create a new Answer.

        :param auth_token:          The authentication token of the acting user
        :type auth_token:           pr_services.models.AuthToken
        :param question_id:         primary key of question to which this answer applies.
        :type question_id:          int
        :param label:               Text for the answer.
        :type label:                unicode
        :param optional_parameters: optional parameters, possibly including:

            * correct
            * end_exam
            * end_question_pool
            * name
            * next_question_pool
            * order
            * text_response
            * value

        :type optional_parameters:  dict or None
        :return:                    Reference to the newly created answer.
        """

        if optional_parameters is None:
            optional_parameters = {}

        question = self._find_by_id(question_id, facade.models.Question)

        a = self.my_django_model(question=question, label=label)
        a.save()
        if optional_parameters:
            facade.subsystems.Setter(auth_token, self, a, optional_parameters)
            a.save()
        self.authorizer.check_create_permissions(auth_token, a)
        return a

# vim:tabstop=4 shiftwidth=4 expandtab
