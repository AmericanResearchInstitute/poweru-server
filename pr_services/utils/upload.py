"""Utils to help facilitate uploads.

:copyright: Copyright 2010 American Research Institute, Inc.

"""

__docformat__ = "restructuredtext en"

from django import forms
from django.core.cache import cache
from django.core.files.uploadhandler import FileUploadHandler
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import Context, RequestContext, loader
from django.views.decorators.cache import never_cache
import facade
import httplib
import logging
from pr_services import exceptions
from pr_services.utils import Utils

def _get_user_from_token(session_id):
    return Utils.get_auth_token_object(session_id).user

def _render_response(request, *args, **kwargs):
    """Similar to render_to_response, but can use the request to create a
    context instance and allow setting a different HTTP status code.

    """
    httpresponse_kwargs = {'mimetype': kwargs.pop('mimetype', None)}
    status = kwargs.pop('status', 200)
    if 'context_instance' not in kwargs:
        kwargs['context_instance'] = RequestContext(request)
    return HttpResponse(loader.render_to_string(*args, **kwargs),
        status=status, **httpresponse_kwargs)

def _render_response_generic(request, title=None, msg=None, status=200):
    c = Context()
    if title is None:
        title = httplib.responses.get(status, 'Unknown')
    c['title'] = str(title)
    if msg is not None:
        c['msg'] = unicode(msg)
    return _render_response(request, '404.html', c, status=status)

def _render_response_ok(*args, **kwargs):
    kwargs['status'] = 200
    return _render_response_generic(*args, **kwargs)

def _render_response_bad_request(*args, **kwargs):
    kwargs['status'] = 400
    return _render_response_generic(*args, **kwargs)

def _render_response_forbidden(*args, **kwargs):
    kwargs['status'] = 403
    return _render_response_generic(*args, **kwargs)

def _render_response_not_found(*args, **kwargs):
    kwargs['status'] = 404
    return _render_response_generic(*args, **kwargs)

def _render_response_server_error(*args, **kwargs):
    kwargs['status'] = 500
    return _render_response_generic(*args, **kwargs)

def _upload_photo(request, actee_manager, actee_index_name, model_photo_storage_engine,
    auth_token=None, actee_index=None):
    """Handle Image file uploads for generic models that have a 'photo' attribute.

    This method will stick the contents of the uploaded file (of which there
    must be exactly 1) onto the filesystem, using Django's "ImageField".

    This method does no validation by design, as that is expected to happen
    in the storage system

    :param request:                     HttpRequest object from Django
    :param actee_manager:               An instance of the manager by which we can look up the actee
    :type actee_manager:                An ObjectManager subclass
    :param actee_index_name:            The key to use on the POST request to find the primary key of the model that we wish to upload
                                        the photo for
    :type actee_index_name:             string
    :param model_photo_storage_engine:  One of the storage engines from storage.py
    :type model_photo_storage_engine:   One of the storage engines from storage.py

    """
    logger = logging.getLogger('utils.upload.upload_photo')

    try:
        if auth_token is None:
            auth_token = request.POST.get('auth_token', None)
        if actee_index is None:
            actee_index = request.POST.get(actee_index_name, None)
        if request.method == 'POST' and len(request.FILES) == 1 and auth_token and actee_index:
            actee = actee_manager._find_by_id(actee_index)
            auth_token = Utils.get_auth_token_object(auth_token)
            facade.subsystems.Authorizer().check_update_permissions(auth_token, actee, {'photo_url' : 'A New Photo!'})
            # save the old photo so we can blow it away on success
            try:
                oldphoto = actee.photo.path
            except ValueError:
                # User has no photo
                oldphoto = None

            # There should only be one file, so a single popitem should
            # provide the photo object tuple. In this, the first item is
            # the form value name, and the second is a list with one entry
            # That entry is our file object.

            # TODO Getting the name of the file input field should be doable.
            # We shouldn't have to assume we have to popitem().
            photo = request.FILES.popitem()[1][0]
            try:
                actee.photo.save(photo.name, photo, save=True)
            # TODO This deserves an explanation.
            except AttributeError:
                actee.photo.save(str(photo), photo, save=True)

            if oldphoto:
                try:
                    model_photo_storage_engine.delete(oldphoto)
                except OSError, e:
                    logger.debug('cannot delete photo %s because it is still in use by another process. This is a Windows-specific error. Please let us know if you see this message on a platform besides Windows.' % (oldphoto))

            return _render_response_ok(request, msg='Image upload successful.')

        else:
            return _render_response_bad_request(request,
                msg='Your request must include exactly one file, the primary key of the object you are uploading the photo for indexed by ' +\
                '\'%s\', and a variable named \'auth_token\'.' % (actee_index_name))
    except exceptions.InvalidImageUploadException, e:
        return _render_response_server_error(request, msg=e.get_error_msg())
    except exceptions.PrException, p:
        return _render_response_forbidden(request, msg=p.get_error_msg())

def upload_csv(request, auth_token=None, model_name=None):
    """Handle CSV file uploads

    This method will stick the contents of the uploaded file (of which there
    must be exactly 1) into the database through a csv_data object.  There is
    currently no validation on this end, but Django will raise an exception
    if you try to upload binary data.

    :param request:   HttpRequest object from Django

    """
    log_prefix = u'pr_services.utils.upload.upload_csv(): '

    logging.debug(log_prefix + 'model name [%s]' % str(model_name))

    if request.method == 'GET':
        if auth_token is None:
            return _render_response_forbidden(request,
                msg='Your request must include an auth token in its URL.')
        if model_name is None:
            return _render_response_bad_request(request,
                msg='Your request must include a model name as the last component of its URL.')
        return _render_response(request, 'upload_csv.html',
            {'title': 'CSV File Upload', 'form': CsvUploadForm(),
            'model_name': model_name, 'auth_token': auth_token})

    elif request.method == 'POST':
        if auth_token is None:
            if 'auth_token' in request.POST:
                auth_token = request.POST['auth_token']
            else:
                return _render_response_forbidden(request,
                    msg='Your request must contain a variable named "auth_token".')

        if len(request.FILES) != 1:
            return _render_response_bad_request(request,
                msg='Your request must include exactly one file.')

        if model_name is None:
            if 'model' in request.POST:
                model_name = request.POST['model']
            else:
                return _render_response_bad_request(request,
                    msg='Your request must include a variable named "model", ' + \
                    'specifying which type of model you are uploading.')

    try:
        auth_token = Utils.get_auth_token_object(auth_token)

        # There should only be one file, so this loop exists just because we don't
        # know the file name under which it is indexed.
        c = None
        for filename in request.FILES:
            c = _process_csv_file(auth_token, request.FILES[filename], model_name)

        return _render_response_ok(request, msg=(str(c) if c else None))
    except exceptions.PrException, p:
        log_message = log_prefix + 'PR exception encountered: '
        if request.method == 'POST':
            if 'auth_token' in request.POST:
                log_message += 'auth_token: [%s]' % request.POST['auth_token']
        log_message += u' error code [%s], message [%s], details [%s]' %\
            (unicode(p.get_error_code()), p.get_error_msg(), unicode(p.get_details()))
        logging.info(log_message)

        return _render_response_forbidden(request, msg=p.get_error_msg())

@transaction.commit_on_success
def _process_csv_file(auth_token, csv_file, model):
    text = csv_file.read()
    text = unicode(text, 'utf-8', 'replace')
    c = facade.models.CSVData(text = text, user = auth_token.user)
    c.save()
    facade.subsystems.Authorizer().check_create_permissions(auth_token, c)
    # If the import manager has a method for importing the plural version of
    # the model name, then use it.  FIXME: This check could eventually look
    # at the verbose_name and verbose_name_plural of all of the available
    # model classes.
    f = getattr(facade.managers.ImportManager(), 'import_%ss' % model, None)
    if f and callable(f):
        return f(auth_token, c)
    else:
        raise exceptions.OperationNotPermittedException('You have selected' +\
            'to upload a CSV for the %s model, which is not supported' % model)

@never_cache
def upload_progress(request):
    """Return JSON object with information about the progress of an upload."""

    progress_id = None
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    elif 'X-Progress-ID' in request.META:
        progress_id = request.META['X-Progress-ID']
    if progress_id:
        # TODO Is there some reason this import shouldn't be at the top?
        from django.utils import simplejson
        cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
        data = cache.get(cache_key)
        json = simplejson.dumps(data)
        return HttpResponse(json)
    else:
        return HttpResponseBadRequest('Server Error: You must provide X-Progress-ID header or query param.')

class FileUploadForm(forms.Form):
    file_ = forms.FileField()

class CsvUploadForm(FileUploadForm):
    pass

class UploadProgressCachedHandler(FileUploadHandler):
    """Tracks progress for file uploads.

    The http post request must contain a header or query parameter, 'X-Progress-ID'
    which should contain a unique string to identify the upload to be tracked.

    """
    def __init__(self, request=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        self.progress_id = None
        self.cache_key = None

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        self.content_length = content_length
        if 'X-Progress-ID' in self.request.GET :
            self.progress_id = self.request.GET['X-Progress-ID']
        elif 'X-Progress-ID' in self.request.META:
            self.progress_id = self.request.META['X-Progress-ID']
        if self.progress_id:
            self.cache_key = "%s_%s" % (self.request.META['REMOTE_ADDR'], self.progress_id)
            cache.set(self.cache_key, {
                'state': 'uploading',
                'length': self.content_length,
                'uploaded' : 0
            })

    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
        pass

    def receive_data_chunk(self, raw_data, start):
        if self.cache_key:
            data = cache.get(self.cache_key)
            data['uploaded'] += self.chunk_size
            cache.set(self.cache_key, data)
        return raw_data

    def file_complete(self, file_size):
        if self.cache_key:
            data = cache.get(self.cache_key)
            data['uploaded'] = file_size
            cache.set(self.cache_key, data, 30)

    def upload_complete(self):
        if self.cache_key:
            data = cache.get(self.cache_key)
            data['state'] = 'done'
            data['uploaded'] = data['length']
            cache.set(self.cache_key, data, 30)
            #cache.delete(self.cache_key)


# vim:tabstop=4 shiftwidth=4 expandtab
