"""
VideoManager class
"""

__docformat__ = "restructuredtext en"

import base64
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse
from django.utils import simplejson as json
import facade
import logging
from pr_services import exceptions
from pr_services import storage
from pr_services import middleware
from pr_services.credential_system.task_manager import TaskManager
from pr_services.rpc.service import service_method
from pr_services.utils import upload
from pr_services.utils import Utils
import traceback
from upload_queue import prepare_upload, queue_upload
from vod_aws.tasks import queue_encoding
from celery.task.sets import subtask
import urlparse
import os.path

class VideoUploadForm(forms.Form):
    video = forms.FileField(label='File')
    name = forms.CharField(label='Title')
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': '4'}))
    author = forms.CharField()


class VideoManager(TaskManager):
    """Manage Videos in the Power Reg system"""

    def __init__(self):
        """ constructor """

        TaskManager.__init__(self)
        self.getters.update({
            'approved_categories' : 'get_general',
            'aspect_ratio' : 'get_general',
            'author' : 'get_general',
            'categories' : 'get_many_to_many',
            'category_relationships' : 'get_many_to_one',
            'create_timestamp' : 'get_time',
            'deleted' : 'get_general',
            'description' : 'get_general',
            'encoded_videos' : 'get_many_to_one',
            'is_ready' : 'get_general',
            'keywords' : 'get_general',
            'length' : 'get_general',
            'live' : 'get_general',
            'name' : 'get_general',
            'num_views' : 'get_general',
            'owner' : 'get_foreign_key',
            'photo_url' : 'get_general',
            'prerequisite_tasks' : 'get_many_to_many',
            'public' : 'get_general',
            'src_file_size' : 'get_general',
            'status' : 'get_general',
            'tags': 'get_tags',
            'users_who_watched' : 'get_general',
        })
        self.setters.update({
            'aspect_ratio' : 'set_general',
            'author' : 'set_general',
            'categories' : 'set_many',
            'description' : 'set_general',
            'encoded_videos' : 'set_many',
            'keywords' : 'set_general',
            'length' : 'set_general',
            'live' : 'set_general',
            'name' : 'set_general',
            'owner' : 'set_foreign_key',
            'photo_url' : 'set_forbidden', # placeholder
            'prerequisite_tasks' : 'set_many',
            'public' : 'set_general',
            'status' : 'set_general',
            'tags' : 'set_tags',
        })
        self.my_django_model = facade.models.Video

    @service_method
    def create(self, auth_token, name, description, author='', categories=[], optional_attributes=None):
        """
        Create a Video task.

        :param auth_token:          The authentication token of the acting user
        :type auth_token:           facade.models.AuthToken
        :param name:                The name of the video to be created.
        :type name:                 string
        :param description:         The description of the video to be created.
        :type description:          string
        :param optional_attributes: A dictionary of optional Video attributes, which may include 'prerequisite_tasks' or
                                    'author'
        :type optional_attributes:  dict
        :return:                    The new Video instance
        """
        if optional_attributes is None:
            optional_attributes = {}
        new_video = self.my_django_model(name=name, description=description,
            author=author)
        if isinstance(auth_token, facade.models.AuthToken):
            new_video.owner = auth_token.user
        new_video.save()
        if optional_attributes:
            facade.subsystems.Setter(auth_token, self, new_video, optional_attributes)
            new_video.save()
        if not len(categories):
            raise exceptions.VideoMustHaveCategory
        for cat in categories:
            facade.models.VideoCategory.objects.create(video=new_video,
                category=self._find_by_id(cat, facade.models.Category))
        self.authorizer.check_create_permissions(auth_token, new_video)
        return new_video

    @service_method
    def delete(self, auth_token, video_id):
        """Mark a video as deleted and remove objects from storage"""
        video = self._find_by_id(video_id)
        self.authorizer.check_delete_permissions(auth_token, video)
        if video.status != 'rejected':
            raise exceptions.OperationNotPermittedException('Videos must be rejected from all categories before they can be deleted.')
        if video.photo.name:
            video.photo.delete()
        for ev in video.encoded_videos.all():
            if ev.file.name:
                ev.file.delete()
            ev.delete()
        video.deleted = True
        video.save()

    @service_method
    def admin_videos_view(self, auth_token):
        videos = self.get_filtered(auth_token, {}, ['author',
            'category_relationships', 'create_timestamp', 'description',
            'encoded_videos', 'length', 'name', 'num_views', 'photo_url',
            'src_file_size'])

        videos = Utils.merge_queries(videos, facade.managers.VideoCategoryManager(), auth_token,
            ['category_name', 'category', 'status'], 'category_relationships')

        return Utils.merge_queries(videos, facade.managers.EncodedVideoManager(), auth_token, 
            ['bitrate', 'http_url', 'url'], 'encoded_videos')

    @service_method
    def user_videos_view(self, auth_token):
        videos = self.get_filtered(auth_token, {}, ['author',
            'approved_categories', 'create_timestamp', 'description',
            'encoded_videos', 'length', 'name', 'num_views', 'photo_url',
            'src_file_size'])

        videos = Utils.merge_queries(videos, facade.managers.CategoryManager(), auth_token,
            ['name'], 'approved_categories')

        return Utils.merge_queries(videos, facade.managers.EncodedVideoManager(), auth_token, 
            ['bitrate', 'url'], 'encoded_videos')
                
    @service_method
    def get_num_views_by_date(self, auth_token, filter=None, requested_attributes=None,
        start_date=None, end_date=None):
        
        """
        This method returns a list of dicts of Videos, as would typically be returned by
        a call to get_filtered(), but also adds an attribute 'num_views'.  This attribute
        normally shows the total number of times a video has been viewed, but in
        this special method it can show how many times a video was viewed inside of the
        specified date range.  This is a bit of an expensive call, because we are taking
        advantage of code reuse by using get_filtered.

        :param auth_token:           The authentication token of the acting user
        :type auth_token:            facade.models.AuthToken
        :param filter:               An optional filter to restrict which videos you want to know about - the same structure passed to get_filtered()
        :type filter:                dict
        :param requested_attributes: A list of attributes to be returned with the results about each video
        :type requested_attributes:  list
        :param start_date:           The start date for the range of dates over which to count the views of the video in question
        :type start_date:            string
        :param end_date:             The end date for the range of dates over which to count the views of the video in question
        :type end_date:              string
        :return:                     A list of dictionaries describing the videos, including the number of views in the date range, indexed by 'num_views'
        """
        if filter is None:
            filter = dict()
        if requested_attributes is None:
            requested_attributes = list()
        elif 'num_views' in requested_attributes:
            # We're going to come behind get_filtered and get the num_views with the date filters, so
            # let's not have it fetch that data this time around
            requested_attributes.remove('num_views')
        video_dicts = self.get_filtered(auth_token, filter, requested_attributes)
        for video_dict in video_dicts:
            try:
                video = self._find_by_id(video_dict['id'])
                self.authorizer.check_read_permissions(auth_token, video, ['num_views'])
                video_dict['num_views'] = video._get_num_views(start_date, end_date)
            except exceptions.PermissionDeniedException:
                # If we get permission denied, just ignore it and continue
                pass
        return video_dicts

    @transaction.commit_manually
    def upload_video(self, request, auth_token=None):
        """Handle video file uploads

        This method will stick the contents of the uploaded file (of which there
        must be exactly 1) into the database through a Video object.  There is
        currently no validation of the Video.

        :param request: HttpRequest object from Django
        :type request:  HttpRequest
        :param auth_token:  AuthToken from an HTML form upload
        :type auth_token:   string or None

        """
        try:
            if request.method == 'GET':
                transaction.rollback()
                if auth_token is None:
                    return upload._render_response_forbidden(request,
                        msg='Your request must include an auth token in its URL.')
                return upload._render_response(request, 'vod_upload_video.html',
                    {'title': 'Video Upload', 'form': VideoUploadForm(),
                     'auth_token': auth_token})
            elif request.method == 'POST':
                if auth_token is None:
                    if 'auth_token' not in request.POST:
                        transaction.rollback()
                        return upload._render_response_forbidden(request,
                            msg='Your request must contain a variable named \'auth_token\'.')
                    else:
                        auth_token = request.POST['auth_token']
                form = VideoUploadForm(data=request.POST, files=request.FILES)
                if form.is_valid():
                    at = Utils.get_auth_token_object(auth_token)
                    at.domain_affiliation.user = at.domain_affiliation.user.downcast_completely()
                    if 'categories' in request.POST:
                        try:
                            categories = json.loads(request.POST['categories'])
                        except ValueError: # Will also handle json.JSONDecodeError, depending on simplejson version used.
                            raise exceptions.InvalidDataException, 'invalid JSON data in categories field'
                        if not isinstance(categories, list):
                            raise exceptions.InvalidDataException, 'categories must be a list of dictionaries mapping "id" to an integer category id'
                        for c in categories:
                            if not (isinstance(c, dict) and
                                'id' in c and
                                type(c['id']) in (int, long)):
                                    raise exceptions.InvalidDataException, 'categories must be a list of dictionaries mapping "id" to an integer category id'
                        categories = [c['id'] for c in categories]
                    new_video = self.create(at,
                        form.cleaned_data['name'],
                        form.cleaned_data['description'],
                        form.cleaned_data['author'],
                        categories)
                    new_video.src_file_size = form.files['video'].size
                    new_video.save()
                    # Commit the transaction before queuing a task to work on
                    # our new Video object.
                    transaction.commit()
                    if getattr(settings, 'VOD_ENABLE_VIDEO_UPLOAD_WORKFLOW', True):
                        ## Queue the task to upload the video to S3.
                        # Let's get the notification URL here because we can do
                        # it accurately while in the web hosting environment
                        # but not in celeryd.
                        notify_url = getattr(settings, 'ENCODING_NOTIFICATION_URL', False)
                        if not notify_url:
                            request = middleware.get_current_request()
                            site = '%s://%s' % (
                                request.is_secure() and 'https' or 'http',
                                request.get_host())
                            notify_url = urlparse.urljoin(site, reverse('vod_aws:video_notification'))
                        pending = prepare_upload(new_video, 'src_file',
                            'video/%d.src' % new_video.id,
                            form.files['video'],
                            callback=subtask(queue_encoding,
                                video_id=new_video.id, notify_url=notify_url))
                        transaction.commit()
                        pending.queue()

                    if 'auth_token' not in request.POST:
                        return upload._render_response_ok(request,
                            msg='Video upload successful.')
                    else:
                        # for plain POST requests (old way), still return the video ID
                        return HttpResponse(str(new_video.id) if new_video else None)
                else:
                    transaction.rollback()
                    logging.info(str(form.errors))
                    return upload._render_response(request, 'vod_upload_video.html',
                        {'title': 'Video Upload', 'form': form,
                         'auth_token': auth_token}, status=400)
        except exceptions.PrException, p:
            transaction.rollback()
            log_message = u'UploadManager.upload_video: pr exception code %d, msg [%s], details [%s]' %\
                (p.get_error_code(), p.get_error_msg(), unicode(p.get_details()))
            logging.info(log_message)
            if p.error_code == 46: # InternalErrorException
                stack_trace = traceback.format_exc()
                logging.info(stack_trace)
                return upload._render_response_server_error(request, msg=p.get_error_msg())
            elif p.error_code in [17, 23, 49, 114, 115, 128]:
                return upload._render_response_forbidden(request, msg=p.get_error_msg())
            else:
                return upload._render_response_bad_request(request, msg=p.get_error_msg())
        except:
            stack_trace = traceback.format_exc()
            logging.info(stack_trace)
            transaction.rollback()
            return upload._render_response_server_error(request, msg='There was an error processing your request.')

    @transaction.autocommit
    def upload_video_photo(self, request):
        """Handle Image file uploads for Video thumbnails.

        We are going to look for a Base64 encoded image if a "photo" file
        doesn't exist in request.FILES and add it onto the request object
        before relegating the request object to the superclass

        Since this method calls a celery task that depends on database changes
        made here, we must ensure that the transaction gets commited first.

        :param request:   HttpRequest object from django
        """
        photo_file = request.FILES.get('photo')
        if photo_file is None:
            # upload_video_photo was called, but without the "photo" file.
            # Let's see if we got a base64 string of the "photo"
            photo_b64 = request.POST.get('photo')
            if photo_b64 is None:
                return upload._render_response_bad_request(request,
                    'Request must include photo file or base64 encoded photo parameter')
            try:
                photo_file = SimpleUploadedFile('photo', base64.b64decode(photo_b64), 'image/png')
                photo_extension = '.png'
            except TypeError:
                # Thrown by b64decode if handed a non base64 string
                return upload._render_response_bad_request(request,
                    'Could not decode uploaded photo parameter')
        else:
            photo_extension = os.path.splitext(photo_file.name)[1]
        auth_token = request.POST.get('auth_token', None)
        video_id = int(request.POST.get('video_id', None))
        if not (request.method == 'POST' and auth_token and video_id):
            return upload._render_response_bad_request(request,
                msg=("Your request must include exactly one file, the "+
                    "'video_id' of the video you are uploading the photo for, "+
                    "and a variable named 'auth_token'."))
        try:
            video = self._find_by_id(video_id)
            auth_token = Utils.get_auth_token_object(auth_token)
            facade.subsystems.Authorizer().check_update_permissions(auth_token,
                video, {'photo_url' : 'A New Photo!'})
            if getattr(settings, 'VOD_ENABLE_VIDEO_UPLOAD_WORKFLOW', True):
                queue_upload(video, 'photo',
                    'video/%d.thumbnail%s' % (video_id, photo_extension),
                    photo_file)
            return upload._render_response_ok(request, msg='Image upload successful.')
        except exceptions.PrException, p:
            return upload._render_response_forbidden(request, msg=p.get_error_msg())

# vim:tabstop=4 shiftwidth=4 expandtab
