"""
EncodedVideoManager class
"""

from django.conf import settings
from pr_services import exceptions
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class EncodedVideoManager(ObjectManager):
    """
    Manage EncodedVideos in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'bitrate' : 'get_general',
            'http_url' : 'get_general',
            'url' : 'get_general',
            'video' : 'get_foreign_key',
        })
        self.setters.update({
            'bitrate' : 'set_general',
        })
        self.my_django_model = facade.models.EncodedVideo

    @service_method
    def create(self, auth_token, bitrate, video_id):
        """
        Create an EncodedVideo object.  This represents an actual Video file that a user can watch.  Because the video can have
        multiple encodings, the meta data is stored commonly on the Video model.

        @param auth_token   The authentication token of the acting user
        @type auth_token    models.AuthToken
        @param bitrate      The bitrate of the EncodedVideo, in kilobits per seconds (kbps)
        @type bitrate       int
        @param video_id     A foreign key to the video object that this encoding is for
        @type video_id      int
        """
        video = self._find_by_id(video_id, facade.models.Video)
        new_encoded_video = self.my_django_model.objects.create(bitrate=bitrate, video=video, owner=auth_token.user)
        self.authorizer.check_create_permissions(auth_token, new_encoded_video)
        return new_encoded_video


# vim:tabstop=4 shiftwidth=4 expandtab
