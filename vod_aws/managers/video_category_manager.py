"""
VideoCategoryManager class
"""

__docformat__ = "restructuredtext en"

import facade
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
from pr_services.utils import Utils

class VideoCategoryManager(ObjectManager):
    """Manage VideoCategories in the Power Reg system"""

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'status' : 'get_general',
            'category_name' : 'get_general',
            'category' : 'get_foreign_key',
            'video' : 'get_foreign_key',
        })
        self.setters.update({
            'status' : 'set_general',
        })
        self.my_django_model = facade.models.VideoCategory


# vim:tabstop=4 shiftwidth=4 expandtab
