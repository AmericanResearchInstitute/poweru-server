"""Custom signals defined by the pr_messaging app."""

from django.dispatch import Signal

# Signal dispatched when there is a new message to be sent (for internal use).
message_ready_to_send = Signal(providing_args=['message_type', 'context', 'sender_', 'recipients'])

# Signal dispatched when the message flags should be updated for the current
# request (for internal use).
message_flags_update = Signal(providing_args=['admins', 'managers', 'all'])

# Signal dispatched by the pr_messaging app to retrieve the Django model
# instance for a given participant.
#
# Handlers for this signal should return an instance of django.db.models.Model
# or None if no instance can be found.
participant_instance_requested = Signal(providing_args=['participant'])

# Signal dispatched by the pr_messaging app to retrieve contact information for
# a given participant and message.
#
# The message_format attribute of the message should be used to determine the
# type of contact info to return or if the participant should receive messages
# of that format at all.
#
# The message_type attribute of the message should be used to determine if the
# participant has enabled or disabled notifications for that message_type.
#
# Handlers for this signal should return one of the following responses:
#   None (to indicate the handler ignored this message or participant)
#   True (to explicitly enable sending this message)
#   False (to explicitly deny sending this message)
#   * (anything else is the participant's contact info)
participant_contact_requested = Signal(providing_args=['participant', 'message'])

# Signal dispatched by the pr_messaging app to retrieve a template for the
# given message instance.
#
# Handlers for this signal should return an object with a render() method that
# expects a single argument of a django.template.Context instance.  The render
# method should return a tuple of (subject, body) if it rendered both message
# parts, or a string if it rendered only the body.  It may return a tuple or
# list with additional elements, which will be added as attachments to the
# message, depending on the backend.  A handler should return None if it cannot
# provide templates for the given message.
message_template_requested = Signal(providing_args=['message'])

# Signal dispatched by the pr_messaging app to perform delivery of the given
# message.
#
# Handlers for this signal should return True if they delivered the message
# successfully, False if they did not, and None if they did nothing with the
# message.
message_ready_for_delivery = Signal(providing_args=['message'])

# Signal dispatched by the pr_messaging app when a message has been delivered.
message_delivered = Signal(providing_args=['message'])
