import logging
import threading
from . import send_message

class MessagingHandler(logging.Handler):
    """Simple logging handler to send messages through the pr_messaging app."""

    def __init__(self, level=logging.NOTSET, **kwargs):
        """Initialize with keyword args that to be passed to send_message."""
        logging.Handler.__init__(self, level)
        self.kwargs = kwargs
        self._thread_local = threading.local()

    def filter(self, record):
        """Filter any log messages generated while sending another one."""
        if not logging.Handler.filter(self, record):
            return 0
        if getattr(self._thread_local, 'emitting', False):
            return 0
        return 1

    def emit(self, record):
        """Update the context and send the message."""
        try:
            self._thread_local.emitting = True
            kwargs = self.kwargs.copy()
            context = kwargs.get('context', {}).copy()
            context['skip_instance_check'] = True
            context['log_level'] = record.levelname
            context['log_message'] = self.format(record)
            kwargs['context'] = context
            send_message(**kwargs)
        except:
            self.handleError(record)
        finally:
            self._thread_local.emitting = False
