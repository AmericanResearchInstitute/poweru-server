"""
FormPage Manager class.
"""

__docformat__ = "restructuredtext en"

# PowerReg
from pr_services import storage
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
from pr_services.utils import upload
import facade

class FormPageManager(ObjectManager):
    """Manage form_pages in the Power Reg system.

    **Attributes:**
     * *exam* -- foreign key for an Exam
     * *number* -- usual meaning of a page number
     * *photo* -- photo, or image, to be displayed
     * *form_widgets* -- FormWidget objects that belong to this photo

    """
    def __init__(self):
        """Constructor."""

        super(FormPageManager, self).__init__()
        self.getters.update({
            'exam' : 'get_foreign_key',
            'form_widgets' : 'get_many_to_one',
            'number' : 'get_general',
            'photo' : 'get_photo_url',
        })
        self.setters.update({
            'exam' : 'set_foreign_key',
            'form_widgets' : 'set_many',
            'number' : 'set_general',
        })
        self.my_django_model = facade.models.FormPage

    @service_method
    def create(self, auth_token, exam, number):
        """
        Create a new FormPage.

        :param auth_token:          The authentication token of the acting user
        :type auth_token:           pr_services.models.AuthToken
        :param exam:                foreign key of exam to which this form_page belongs.
        :type exam:                 int
        :param number:              the usual meaning of a page number
        :type number:               int
        :return:                    Reference to the newly created form_page.
        """

        exam_object = self._find_by_id(exam, facade.models.Exam)

        form_page = self.my_django_model.objects.create(exam=exam_object, number=number)
        self.authorizer.check_create_permissions(auth_token, form_page)
        return form_page

    def upload_form_photo(self, request):
        """Handle Image file uploads for FormPage photos

        :param request:    HttpRequest object from django

        """
        return upload._upload_photo(request, self, 'form_page_id', storage.FormPagePhotoStorage())

# vim:tabstop=4 shiftwidth=4 expandtab
