"""Signal handlers for the pr_messaging app."""

import logging
import uuid as uuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
import django.core.signals
from .models import MessageTemplate, SentMessage, SentMessageParticipant
from .queue import queue
from . import signals

logger = logging.getLogger('pr_messaging.handlers')

def request_started(sender, **kwargs):
    logger.trace('request_started sender=%r kwargs=%r', sender, kwargs)
    return queue.request_started(sender, **kwargs)

def request_finished(sender, **kwargs):
    logger.trace('request_finished sender=%r kwargs=%r', sender, kwargs)
    return queue.request_finished(sender, **kwargs)

def got_request_exception(sender, **kwargs):
    logger.trace('got_request_exception sender=%r kwargs=%r', sender, kwargs)
    return queue.got_request_exception(sender, **kwargs)

def message_ready_to_send(sender, **kwargs):
    logger.trace('message_ready_to_send sender=%r kwargs=%r', sender, kwargs)
    kwargs.pop('signal', None)
    return queue.send_message(sender, **kwargs)

def message_flags_update(sender, **kwargs):
    return queue.enable_messages(sender, **kwargs)

def participant_instance_requested(sender, **kwargs):
    logger.trace('participant_instance_requested sender=%r kwargs=%r', sender, kwargs)
    if getattr(settings, 'MESSAGING_PARTICIPANT_INSTANCE_HANDLER', True):
        return default_participant_instance_handler(sender, **kwargs)

def default_participant_instance_handler(sender, **kwargs):
    participant = kwargs.get('participant', None)
    if participant and 'django.contrib.auth' in settings.INSTALLED_APPS:
        from django.contrib.auth.models import User
        try:
            if participant.username:
                return User.objects.get(username=participant.username)
            elif participant.email:
                return User.objects.get(email=participant.email)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            pass

def participant_contact_requested(sender, **kwargs):
    logger.trace('participant_contact_requested sender=%r kwargs=%r', sender, kwargs)
    if getattr(settings, 'MESSAGING_PARTICIPANT_CONTACT_HANDLER', True):
        return default_participant_contact_handler(sender, **kwargs)

def default_participant_contact_handler(sender, **kwargs):
    participant = kwargs.get('participant', None)
    message = kwargs.get('message', None)
    if participant and message:
        if 'email' in message.message_format:
            # Example of denying other messaging formats.
            #if message.message_format != 'email':
            #    return False
            if participant.email is None and participant.is_sender:
                return settings.DEFAULT_FROM_EMAIL
            elif participant.email and participant.fullname:
                return u'%s <%s>' % (participant.fullname, participant.email)
            elif participant.email:
                return participant.email

def participant_contact_handler_filter(sender, **kwargs):
    """Filter whether a message is sent based on flags set by the queue."""
    return
    # FIXME
    logger.trace('participant_contact_handler_filter sender=%r kwargs=%r', sender, kwargs)
    participant = kwargs.get('participant', None)
    message = kwargs.get('message', None)
    if participant and message:
        if not getattr(message, 'send_to_all', True):
            return False
        if participant.email and not participant.is_sender:
            [x[1] for x in settings.ADMINS]
            if getattr(message, 'send_to_admins', True):
                pass

def message_template_requested(sender, **kwargs):
    logger.trace('message_template_requested sender=%r kwargs=%r', sender, kwargs)
    if getattr(settings, 'MESSAGING_TEMPLATE_HANDLER', True):
        return default_template_handler(sender, **kwargs)

def default_template_handler(sender, **kwargs):
    message = kwargs.get('message', None)
    try:
        mt = MessageTemplate.objects.get(message_type__slug=message.message_type,
                                         message_format__slug=message.message_format)
    except MessageTemplate.DoesNotExist:
        logger.error('no template found for given message type and format')
    else:
        return mt

def message_ready_for_delivery(sender, **kwargs):
    logger.trace('message_ready_for_delivery sender=%r kwargs=%r', sender, kwargs)
    if getattr(settings, 'MESSAGING_DELIVERY_HANDLER', True):
        return default_delivery_handler(sender, **kwargs)

def default_delivery_handler(sender, **kwargs):
    message = kwargs.get('message', None)
    if message and 'email' in message.message_format:
        msg = EmailMultiAlternatives()
        msg.subject = message.subject
        msg.body = message.body
        if message.sender():
            msg.from_email = message.sender().contact_info
        msg.to = [r.contact_info for r in message.recipients() if r.role == 'to']
        # FIXME: Django doesn't yet support the CC field, so just add CC'ed
        # recipients in the To: field for now.
        msg.to += [r.contact_info for r in message.recipients() if r.role == 'cc']
        msg.bcc = [r.contact_info for r in message.recipients() if r.role == 'bcc']
        for attachment in getattr(message, 'attachments', []):
            if isinstance(attachment, (list, tuple)):
                if len(attachment) >= 1 and attachment[0] is None:
                    msg.attach_alternative(*attachment[1:])
                else:
                    msg.attach(*attachment)
            else:
                msg.attach(attachment)
        return msg.send()

def message_delivered(sender, **kwargs):
    logger.trace('message_delivered sender=%r kwargs=%r', sender, kwargs)
    if getattr(settings, 'MESSAGING_DELIVERED_HANDLER', True):
        return default_delivered_handler(sender, **kwargs)

def default_delivered_handler(sender, **kwargs):
    message = kwargs.get('message', None)
    message_template_pk = getattr(message, 'message_template_pk', None)
    if message and message_template_pk:
        sent_message = SentMessage.objects.create(message_template_id=message_template_pk)
        for participant in message.participants:
            sent_message_participant = SentMessageParticipant(sent_message=sent_message)
            sent_message_participant.role = participant.role
            sent_message_participant.participant = participant.instance
            sent_message_participant.participant_contact = participant.contact_info
            sent_message_participant.save()


# Add the dispatch_uid when connecting a signal.
_connect = lambda x, y: x.connect(y, dispatch_uid=str(uuid.uuid4()))

# Connect handlers to Django request signals.
_connect(django.core.signals.request_started, request_started)
_connect(django.core.signals.request_finished, request_finished)
_connect(django.core.signals.got_request_exception, got_request_exception)

# Connect handlers to our own internal signals.
_connect(signals.message_ready_to_send, message_ready_to_send)
_connect(signals.message_flags_update, message_flags_update)
_connect(signals.participant_instance_requested, participant_instance_requested)
_connect(signals.participant_contact_requested, participant_contact_requested)
_connect(signals.participant_contact_requested, participant_contact_handler_filter)
_connect(signals.message_template_requested, message_template_requested)
_connect(signals.message_ready_for_delivery, message_ready_for_delivery)
_connect(signals.message_delivered, message_delivered)
