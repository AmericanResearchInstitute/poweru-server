from django.conf.urls.defaults import patterns, url
import facade
import vod_aws.views

urlpatterns = patterns('',
    # Video upload entry points
    url(r'^(?P<auth_token>[A-Za-z0-9]{32})/upload_video$',
        facade.managers.VideoManager().upload_video,
        name='upload_video_form'),
    url(r'^upload_video$', facade.managers.VideoManager().upload_video, name='upload_video'),

    # Video encoding notification
    url(r'^video_notification$', vod_aws.views.video_notification, name='video_notification'),

    # Video Photo file upload entry point
    url(r'^upload_video_photo', facade.managers.VideoManager().upload_video_photo,
        name='upload_video_photo'),
)
