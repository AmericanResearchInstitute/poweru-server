from django.conf.urls.defaults import *
from django.conf import settings
import facade
from pr_services.rpc import xmlrpc, amf
from pr_services.scorm_system import scorm_server
from pr_services.utils import upload
import pr_services.views as pr_views

urlpatterns = patterns('',
    # Blank Page for the index
    (r'^$', pr_views.blank_page),

    # AMF RPC gateway for flex consumers
    (r'^amf', amf.gateway),

    # XML RPC gateway for generic consumers
    (r'^xmlrpc', xmlrpc.gateway),

    # file upload progress
    url(r'^upload_progress$', upload.upload_progress, name='upload_progress'),

    # CSV file upload entry points
    url(r'^auth_token/(?P<auth_token>[A-Za-z0-9]+)/upload_csv/(?P<model_name>[A-Za-z0-9]+)/$',
        upload.upload_csv,
        name='upload_csv_form'),
    url(r'^upload_csv', upload.upload_csv),

    # this is a fairly stupid view that sends back a CSV file based on
    # its input
    url(r'^export_csv', pr_views.export_csv),

    # URL sent via email which allows user to confirm their email address.
    url(r'^confirm_email/(?P<confirmation_code>[A-Fa-f0-9]{40})/$',
        pr_views.confirm_email, name='confirm_email'),

    # SCORM course upload entry point
    (r'^upload_scorm_course', facade.managers.ScoManager().upload_course),

    # User Photo file upload entry points
    url(r'^auth_token/(?P<auth_token>[A-Za-z0-9]+)/upload/user/photo/user/id/(?P<user_id>[0-9]+)/$', 
        facade.managers.UserManager().upload_user_photo,
        name='upload_user_photo_form'),
    url(r'^upload/user/photo',
        facade.managers.UserManager().upload_user_photo),

    # Organization Photo file upload entry point
    (r'^upload/organization/photo', facade.managers.OrganizationManager().upload_organization_photo),

    (r'^cookiecache/([A-Za-z0-9]+)/$', pr_views.cookiecache),

    #################################################################
    # Let there be SCORM! (And it was good)
    #################################################################
    # This is how we will start the player for a user
    url(r'^scorm_player/(?P<auth_token>[A-Za-z0-9]+)/(?P<sco_id>\d+)/$', scorm_server.ScormServer().return_player, name='scorm_player'),

    # This is how the LMSCommit() data will be saved to our system
    url(r'^scorm_player/lms_commit$', scorm_server.ScormServer().lms_commit, name='lms_commit'),

    # This is the form that the SCORM player will use to store data and submit it to us
    url(r'^scorm_player/db_post_form/(?P<auth_token>[A-Za-z0-9]+)/(?P<sco_session_id>\d+)/(?P<shared_object>.*)/$', scorm_server.ScormServer().db_post_form,
        name='db_post_form'),
    url(r'^scorm_player/db_post_form/(?P<auth_token>[A-Za-z0-9]+)/(?P<sco_session_id>\d+)/$', scorm_server.ScormServer().db_post_form,
        name='db_post_form'),

    #################################################################
    # URLs for plugins
    #################################################################
    # We're using the namespace so we can reliabily use
    # django.core.urlresolvers.reverse() for plugin views.
    #(r'^vod_aws/', include('vod_aws.urls', namespace='vod_aws')),
)

if 'ecommerce' in settings.INSTALLED_APPS:
    from ecommerce.paypal_svc import express_checkout
    import ecommerce.views as ecommerce_views

    urlpatterns += patterns('',
        # Users are directed here from paypal's Express Checkout site
        (r'^express_checkout/success/', ecommerce_views.express_checkout_successful_return),

        # Users are directed here from paypal's Express Checkout site
        (r'^express_checkout/cancel/', ecommerce_views.express_checkout_unsuccessful_return),
    )

if 'vod_aws' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^vod_aws/', include('vod_aws.urls', namespace='vod_aws')),
    )

# vim:tabstop=4 shiftwidth=4 expandtab
