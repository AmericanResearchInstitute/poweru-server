# A WSGI application, suitable for use with mod_wsgi in Apache as a WSGIScript
# target. The WSGI PYTHONPATH must be configured properly for this to work

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings' 

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

def application(environ, start_response):
    '''Prepares and returns a django wsgi application.

    This assumes that the python path has been properly prepared 
    prior to execution'''


    return WSGIHandler()(environ, start_response)

# If DEBUG is set, kindly wrap the application in Paste's ErrorMiddleware
# to catch unhandled exceptions and display them
if settings.DEBUG:
    from paste.exceptions.errormiddleware import ErrorMiddleware
    application = ErrorMiddleware(application, debug=True)

# vim:tabstop=4 shiftwidth=4 expandtab syn=python
