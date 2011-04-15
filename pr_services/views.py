"""
@copyright Copyright 2009 American Research Institute, Inc.
"""

import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.utils import simplejson as json
import utils
import facade
from pr_services import exceptions


_logger = logging.getLogger('pr_services.views')

def blank_page(request):
    """
    Render a blank page. This is useful at, say, the web root of a project
    that only services requests via RPC. 
    """
    return HttpResponse('')

def cookiecache(request, auth_token):
    """
    Look up an entry in the CachedCookie database table.
    
    @param request the request
    @type request django.http.HttpRequest
    @param auth_token auth token string
    @type auth_token string
    """
    
    response = HttpResponse(mimetype='text/plain')
    
    try:
        cached_cookie = facade.models.CachedCookie.objects.get(key=auth_token)
        response.write(cached_cookie.value)
    except facade.models.CachedCookie.DoesNotExist:
        logging.info(u'pr_services.views.cookiecache: lookup for non-existent auth token [%s]' % auth_token)
        response.write('')
    
    return response

def export_csv(request):
    if request.method != 'POST':
        _logger.error('export_csv: non-POST request')
        return HttpResponseBadRequest('request must use POST method')
    if not 'data' in request.POST:
        _logger.error('export_csv: no "data" parameter')
        return HttpResponseBadRequest('request must include a "data" parameter')
    
    data = json.loads(request.POST['data'])
    if not isinstance(data, list):
        _logger.error('export_csv: request.POST["data"] did not deserialize to a list')
        return HttpResponseBadRequest('request.POST["data"] did not deserialize to a list')
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=report.csv'
    
    writer = utils.UnicodeCsvWriter(response)
    for item in data:
        if not isinstance(item, list):
            _logger.error('export_csv: an item in the "data" array was not an array!')
            return HttpResponseBadRequest('an item in the "data" array was not an array!')
        writer.writerow(item)
    
    return response

def confirm_email(request, confirmation_code):
    try:
        auth_token = facade.managers.UserManager().confirm_email(confirmation_code)
    except exceptions.UserConfirmationException, e:
        return HttpResponseBadRequest(unicode(e))
    response = HttpResponseRedirect(getattr(settings, 'FRONTEND_URL', '/'))
    if auth_token:
        response.set_cookie('authToken', unicode(auth_token))
    return response
