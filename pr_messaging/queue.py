"""Thread-safe queue to store messages during a request."""

from threading import local
from .tasks import process_messages
from .common import Message

class MessageQueue(local):
    """Internal thread local queue to store messages during a request."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.messages = []
        self.in_request = False
        self.send_to_admins = True
        self.send_to_managers = True
        self.send_to_all = True

    def request_started(self, sender, **kwargs):
        self.reset()
        self.in_request = True

    def request_finished(self, sender, **kwargs):
        self.in_request = False
        if self.messages:
            process_messages.delay(self.messages)
        self.reset()

    def got_request_exception(self, sender, **kwargs):
        self.in_request = False
        self.reset()

    def send_message(self, sender, **kwargs):
        kwargs['sender'] = kwargs.pop('sender_', None)
        if self.in_request:
            kwargs['send_to_admins'] = self.send_to_admins
            kwargs['send_to_managers'] = self.send_to_managers
            kwargs['send_to_all'] = self.send_to_all
            self.messages.append(Message(**kwargs))
        else:
            process_messages.delay([Message(**kwargs)])

    def enable_messages(self, sender, **kwargs):
        self.send_to_admins = kwargs.get('admins', self.send_to_admins)
        self.send_to_managers = kwargs.get('managers', self.send_to_managers)
        self.send_to_all = kwargs.get('all', self.send_to_all)

# This queue instance can be used by multiple threads without a problem, since
# it inherits from threading.local.
queue = MessageQueue()
