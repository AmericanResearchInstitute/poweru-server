"""Celery tasks for processing messages."""

import logging
from django.conf import settings
from django.template import Context
from celery.decorators import task
from .models import MessageTemplate, MessageFormat, MessageType
from . import signals

logger = logging.getLogger('pr_messaging.tasks')

# task should accept a message list as created by messaging.Queue.

# load each template model, and if it is not active, skip it
# if template is not found, don't worry. just skip it

# if template is a multi-signal template, put all messages of that type together in a list and render that list into the context

# render templates with context and send. Add sender and recipient name and email to the context

# create a SentMessage record for each message sent. If sender and/or recipient
# is an instance of models.Model, save their reference to the corresponding
# GenericForeignKey field.


@task(ignore_result=True)
def process_messages(messages=[]):
    """
    Celery task for processing a list of messages.
    """
    logger.trace('process_messages %r', messages)
    # FIXME: Handle multiple messages with the same type by aggregating the context.
    for message in messages:
        # Retrieve the corresponding message type for this message.
        try:
            message_type = MessageType.objects.get(slug=message.message_type, enabled=True)
        except MessageType.DoesNotExist:
            logger.error('no enabled message type found for %r', message)
            continue
        # If this message type supports rendering once for multiple recipients,
        # don't split it. Otherwise, split it into separate message instances
        # for each recipient.
        if len(message.recipients()) == 0:
            logger.warning('skipping message with no recipients')
        elif len(message.recipients()) == 1 or message_type.multiple_recipients:
            for message_format in MessageFormat.objects.filter(enabled=True):
                new_message = message.updated(message_format=message_format.slug)
                update_message_participants.delay(new_message)
        else:
            process_messages.delay(message.split_by_recipient())

@task(ignore_result=True)
def update_message_participants(message):
    """
    Celery task to retrieve contact info for each participant in a message and
    determine whether the message should be sent to each participant.
    """
    logger.trace('update_message_participants %r', message)
    default_send = True
    new_participants = []
    for p in message.participants:
        responses = signals.participant_contact_requested.send_robust(None, \
            participant=p, message=message)
        should_send = []
        contact_info = None
        for receiver, response in responses:
            if response is None:
                continue
            elif isinstance(response, Exception):
                logger.error('received exception %r from %r', response, receiver)
                continue
            elif response is False:
                should_send.append(False)
            elif response is True:
                should_send.append(True)
            else:
                contact_info = response
        if default_send:
            # Default to sending unless explicitly denied.
            should_send = all(should_send)
        else:
            # Default to not sending unless explicitly allowed.
            should_send = all(should_send) and any(should_send)
        if should_send and contact_info:
            new_participants.append(p.updated(contact_info=contact_info))
    new_message = message.updated(participants=new_participants)
    if new_message.recipients():
        render_message.delay(new_message)

@task(ignore_result=True)
def render_message(message):
    """
    Celery task for rendering the message subject and body with the appropriate
    template based on the message type and format.
    """
    logger.trace('render_message %r', message)
    # Send the message_template_requested signal to find appropriate subject
    # and body templates for the given message.
    responses = signals.message_template_requested.send_robust(None, message=message)
    template = None
    for receiver, response in responses:
        if response is None:
            continue
        elif isinstance(response, Exception):
            logger.error('received exception %r from %r', response, receiver)
            continue
        elif response and callable(getattr(response, 'render', None)):
            template = response
    # Now render the subject and body with the message context, then pass the
    # message along for delivery
    if template:
        if isinstance(template, MessageTemplate):
            message = message.updated(message_template_pk=template.pk)
        context = Context(dict(message.context.items()))
        context['message'] = message
        context['frontend_url'] = getattr(settings, 'FRONTEND_URL', '').rstrip('/')
        context['backend_url'] = getattr(settings, 'BACKEND_URL', '').rstrip('/')
        try:
            result = template.render(context)
        except:
            logger.exception('template.render')
        if isinstance(result, basestring):
            subject, body, attachments = '', result, []
        elif isinstance(result, (list, tuple)) and len(result) >= 2:
            subject, body, attachments = result[0], result[1], result[2:]
        else:
            logger.error('unable to handle render() result %r', result)
            return
        new_message = message.updated(subject=subject, body=body,
                                      attachments=attachments)
        deliver_message.delay(new_message)
    else:
        logger.error('no template found for given message type and format')

@task(ignore_result=True)
def deliver_message(message):
    """
    Celery task for performing the actual message delivery.
    """
    logger.trace('deliver_message %r', message)
    responses = signals.message_ready_for_delivery.send_robust(None, message=message)
    for receiver, response in responses:
        if response is None:
            continue
        elif isinstance(response, Exception):
            logger.error('received exception %r from %r', response, receiver)
            continue
        elif response:
            # Currently we don't care about the responses from this signal.
            signals.message_delivered.send_robust(receiver, message=message)
        else:
            logger.error('receiver %r failed to send message %r', receiver, message)
