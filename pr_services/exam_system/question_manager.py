"""
Question Manager class.
"""

__docformat__ = "restructuredtext en"

# PowerReg
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class QuestionManager(ObjectManager):
    """
    Manage questions in the Power Reg system.

    **Attributes:**
     * *answers* -- List of foreign keys for Answer objects.
     * *rejoinder* -- Text to display when someone gets this question wrong.
     * *help_text* -- Help text for this question.
     * *label* -- Text of the question.
     * *max_answers* -- Maximum number of answers that may be selected (for choice questions).
     * *min_answers* -- Minimum number of answers that must be selected (for choice questions).
     * *max_length* -- Maximum length of text entry allowed.
     * *min_length* -- Minimum length of text entry required.
     * *max_value* -- Maximum valid value for any numeric question type.
     * *min_value* -- Minimum valid value for any numeric question type.
     * *name* -- Unique name for this question within the exam.
     * *order* -- Order of this question within the question pool.
     * *question_pool* -- Reference to the question pool containing this question.
     * *question_type* -- Type of question.
     * *required* -- Is the user required to answer this question?
     * *responses* -- List of foreign keys for Response objects.
     * *text_regex* -- Regular expression used to validate text entry.
     * *text_response* -- Do we allow a free-form, text response regardless of the answer?
     * *text_response_label* -- Additional label to be displayed for free-text response.
     * *user* -- User who is being evaluated (for ratings).
     * *widget* -- Widget used to display this question.
    """

    def __init__(self):
        """Constructor."""

        super(QuestionManager, self).__init__()
        self.getters.update({
            'answers': 'get_many_to_one',
            'help_text': 'get_general',
            'label': 'get_general',
            'max_answers': 'get_general',
            'min_answers': 'get_general',
            'max_length': 'get_general',
            'min_length': 'get_general',
            'max_value': 'get_general',
            'min_value': 'get_general',
            'name': 'get_general',
            'order': 'get_general',
            'question_pool': 'get_foreign_key',
            'question_type': 'get_general',
            'rejoinder': 'get_general',
            'required': 'get_general',
            'responses': 'get_many_to_one',
            'text_regex': 'get_general',
            'text_response': 'get_general',
            'text_response_label': 'get_general',
            'user': 'get_foreign_key',
            'widget': 'get_general',
        })
        self.setters.update({
            'answers': 'set_many',
            'answers': 'set_many',
            'help_text': 'set_general',
            'label': 'set_general',
            'max_answers': 'set_general',
            'min_answers': 'set_general',
            'max_length': 'set_general',
            'min_length': 'set_general',
            'max_value': 'set_general',
            'min_value': 'set_general',
            'name': 'set_general',
            'order': 'set_general',
            'question_pool': 'set_foreign_key',
            'question_type': 'set_general',
            'rejoinder': 'set_general',
            'required': 'set_general',
            'responses': 'set_many',
            'text_regex': 'set_general',
            'text_response': 'set_general',
            'text_response_label': 'set_general',
            'user': 'set_foreign_key',
            'widget': 'set_general',
        })
        self.my_django_model = facade.models.Question

    @service_method
    def create(self, auth_token, question_pool_id, question_type, label,
               optional_parameters=None):
        """
        Create a new question.
        
        :param auth_token:          The authentication token of the acting user
        :type auth_token:           pr_services.models.AuthToken
        :param question_pool_id:    primary key of question pool containing this question.
        :type question_pool_id:     int
        :param question_type:       Type of question.
        :type question_type:        unicode, must be one of the following options:

            * bool
            * char
            * choice
            * date
            * datetime
            * decimal
            * float
            * int
            * rating
            * text
            * time

        :param label:               Label for the question.
        :type label:                unicode
        :param optional_parameters: optional parameters, possibly including:

            * answers
            * help_text
            * max_answers
            * min_answers
            * max_length
            * min_length
            * max_value
            * min_value
            * name
            * order
            * rejoinder
            * required
            * text_regex
            * text_response
            * text_response_label
            * widget

        :type optional_parameters:  dict or None
        :return:                    Reference to the newly created question.
        """

        if optional_parameters is None:
            optional_parameters = {}
            
        question_pool = self._find_by_id(question_pool_id, facade.models.QuestionPool)

        q = self.my_django_model(question_pool=question_pool,
                                 question_type=question_type, label=label)
        q.save()
        if optional_parameters:
            facade.subsystems.Setter(auth_token, self, q, optional_parameters)
            q.save()
        self.authorizer.check_create_permissions(auth_token, q)
        return q

# vim:tabstop=4 shiftwidth=4 expandtab
