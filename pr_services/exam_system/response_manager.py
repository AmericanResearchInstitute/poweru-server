"""
Response Manager class.
"""

__docformat__ = "restructuredtext en"

# PowerReg
from pr_services.object_manager import ObjectManager
import facade

class ResponseManager(ObjectManager):
    """
    Manage responses to exam questions in the Power Reg system.

    **Attributes:**
     * *answer* -- Which answer(s) the user chose for multiple choice questions.
     * *correct* -- Whether this response is correct, None if we havent' checked yet.
     * *exam_session* -- The exam session associated with this response.
     * *question* -- The question associated with this response.
     * *text* -- Free-form text response if entered by the user.
     * *value* -- Value of the response, depending on the question type.
     * *valid* -- Whether this response is valid, None if we haven't checked yet.
    """

    def __init__(self):
        """Constructor."""

        super(ResponseManager, self).__init__()
        self.getters.update({
            'answers': 'get_many_to_many',
            'correct': 'get_general',
            'exam_session': 'get_foreign_key',
            'question': 'get_foreign_key',
            'text': 'get_general',
            'valid': 'get_general',
            'value': 'get_general',
        })
        self.my_django_model = facade.models.Response

# vim:tabstop=4 shiftwidth=4 expandtab
