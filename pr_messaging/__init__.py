"""Signal initialization and helper functions."""

from . import signals as _signals

# Helper functions for use by other apps.
def send_message(**kwargs):
    if 'sender' in kwargs:
        kwargs['sender_'] = kwargs.pop('sender')
    sender = kwargs.pop('_sender', send_message)
    responses = _signals.message_ready_to_send.send(sender, **kwargs)
    return any([r[1] for r in responses])

def message_admins(**kwargs):
    from django.conf import settings
    kwargs['sender'] = settings.SERVER_EMAIL
    kwargs['recipients'] = list(settings.ADMINS)
    return send_message(_sender=message_admins, **kwargs)

def message_managers(**kwargs):
    from django.conf import settings
    kwargs['sender'] = settings.SERVER_EMAIL
    kwargs['recipients'] = list(settings.MANAGERS)
    return send_message(_sender=message_managers, **kwargs)

def enable_messages(**kwargs):
    responses = _signals.message_flags_update.send(enable_messages, **kwargs)
    return any([r[1] for r in responses])
