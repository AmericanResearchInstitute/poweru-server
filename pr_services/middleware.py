# Based on: http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()

def get_current_request():
    """
    Return the current request object from thread local storage.
    """
    return getattr(_thread_locals, 'request', None)

class ThreadLocal(object):
    """
    Middleware that stores the request object to thread local storage.
    """

    def process_request(self, request):
        """
        Store the request objects on the incoming request.
        """
        _thread_locals.request = request

    def process_response(self, request, response):
        """
        Remove the request object from this thread after the request.
        """
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response
