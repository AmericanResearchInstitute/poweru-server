"""
FormWidget Manager class.
"""

__docformat__ = "restructuredtext en"

# PowerReg
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class FormWidgetManager(ObjectManager):
    """
    Manage form_widgets in the Power Reg system.

    **Attributes:**
     * *answer* -- foreign key for an Answer, used only for multiple-choice scenarios
     * *question* -- foreign key for a Question
     * *form_page* -- foreign key for a FormPage
     * *height* -- height of the widget in pixels
     * *width* -- width of the widget in pixels
     * *x* -- x coordinate for the widget
     * *y* -- y coordinate for the widget
    """

    def __init__(self):
        """Constructor."""

        super(FormWidgetManager, self).__init__()
        self.getters.update({
            'answer' : 'get_foreign_key',
            'form_page' : 'get_foreign_key',
            'question' : 'get_foreign_key',
            'height' : 'get_general',
            'width' : 'get_general',
            'x' : 'get_general',
            'y' : 'get_general',
        })
        self.setters.update({
            'answer' : 'set_foreign_key',
            'form_page' : 'set_foreign_key',
            'question' : 'set_foreign_key',
            'height' : 'set_general',
            'width' : 'set_general',
            'x' : 'set_general',
            'y' : 'set_general',
        })
        self.my_django_model = facade.models.FormWidget

    @service_method
    def create(self, auth_token, form_page, height, width, x, y, question, answer=None):
        """
        Create a new FormWidget.

        :param auth_token:          The authentication token of the acting user
        :type auth_token:           pr_services.models.AuthToken
        :param form_page:           foreign key of form_page to which this form_widget belongs.
        :type form_page:            int
        :param height:              height of the widget in pixels
        :type height:               int
        :param width:               width of the widget in pixels
        :type width:                int
        :param x:                   x coordinate for the widget
        :type width:                int
        :param y:                   y coordinate for the widget
        :type width:                int
        :return:                    Reference to the newly created form_widget.
        """

        form_page_object = self._find_by_id(form_page, facade.models.FormPage)
        question_object = self._find_by_id(question, facade.models.Question)

        form_widget = self.my_django_model(form_page=form_page_object,
                question=question_object, height=height, width=width, x=x, y=y)
        if answer is not None:
            form_widget.answer = self._find_by_id(answer, facade.models.Answer)

        form_widget.save()

        self.authorizer.check_create_permissions(auth_token, form_widget)
        return form_widget

# vim:tabstop=4 shiftwidth=4 expandtab
