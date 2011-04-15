"""Common objects passed around by various parts of the pr_messaging app."""

import copy
import re
from django.db import models
from django.contrib.contenttypes.models import ContentType
from .signals import participant_instance_requested

class Immutable(object):
    """
    An immutable base class initialized from keyword arguments.
    
    Objects that are passed around between signal handlers and tasks should be
    treated as immutable and never modified once created, since the same
    instance may be passed to multiple receivers.  Instead, a new modified
    instance can be created using the update(**kwargs) method.  All current
    attributes are preserved, except for those changed or added via the keyword
    arguments.
    """

    def __setattr__(self, *args):
        raise TypeError("can't modify immutable instance")
    __delattr__ = __setattr__

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            super(Immutable, self).__setattr__(key, copy.copy(value))

    def updated(self, **kwargs):
        """Return a copy of this instance with modified attributes."""
        for key, value in self.__dict__.iteritems():
            kwargs.setdefault(key, value)
        return type(self)(**kwargs)

    def clone(self):
        """Return an exact copy of this instance."""
        return self.updated()

    def __repr__(self):
        attrs = []
        for key, value in self.__dict__.iteritems():
            if value:
                attrs.append(u'%s=%s' % (key, repr(value)))
        return u'<%s %s>' % (type(self).__name__, ' '.join(attrs))

class Participant(Immutable):
    """
    Stores information about a pr_messaging participant.
    
    The participant argument to the constructor can be specified in any of the
    following forms:
        "joe"
        "joe@user.com"
        "<joe@user.com>"
        "Joe User <joe@user.com>"
        ("Joe User", "joe@user.com")
        User(username='joe', first_name='Joe', last_name='User',
             email='joe@user.com')
        Participant(other_participant)

    Each participant should also be created with a "role" keyword argument to
    indicate the participant's role in relation to the message.  The "role"
    should be one of "from", "to", "cc", or "bcc".

    Specifying a participant of None for the sender of a message will try to
    use the "system" account for the corresponding message type.
    """

    def _init_with_participant(self, participant, **kwargs):
        instance = None
        username = None
        fullname = None
        email = None
        # If participant is given as a string, determine if it is an email
        # address, email address with a full name, or just a username.
        if isinstance(participant, basestring):
            if '@' in participant:
                match = re.match(r'^(.*?)\<(.+?\@.+?)\>.*$', participant)
                if match:
                    email = unicode(match.group(2))
                    fullname = unicode(match.group(1)).strip() or None
                else:
                    email = unicode(participant)
            else:
                username = unicode(participant)
        # If participant is given as a tuple, it is expected that the first
        # item is the full name and the second is the email address.
        elif isinstance(participant, (list, tuple)) and len(participant) >= 2:
            fullname = unicode(participant[0])
            email = unicode(participant[1])
        # If participant is a model instance, look at its attributes later.
        elif isinstance(participant, models.Model):
            instance = participant
        # Copy constructor
        elif isinstance(participant, type(self)):
            return participant.__dict__
        else:
            raise TypeError, 'unknown participant specification'
        kwargs['username'] = username
        kwargs['fullname'] = fullname
        kwargs['email'] = email
        # If an instance wasn't given, try to find a corresponding model
        # instance based on the information provided so far by dispatching the
        # participant_instance_requested signal.
        if instance is None and not kwargs.get('skip_instance_check', False):
            p = type(self)(**kwargs)
            responses = participant_instance_requested.send_robust(None, participant=p)
            for receiver, response in responses:
                if isinstance(response, models.Model):
                    instance = response
                    break
                else:
                    continue
        # If an instance has been associated with this participant, look for
        # its username and email attributes, and a get_full_name() method,
        # assuming the model is an instance of django.contrib.auth.models.User.
        if instance is not None:
            if kwargs['username'] is None and hasattr(instance, 'username'):
                kwargs['username'] = instance.username
            if kwargs['email'] is None and hasattr(instance, 'email'):
                kwargs['email'] = instance.email
            if kwargs['fullname'] is None and \
                    callable(getattr(instance, 'get_full_name', None)):
                kwargs['fullname'] = instance.get_full_name()
            ct = ContentType.objects.get_for_model(instance)
            kwargs['content_type'] = '%s.%s' % (ct.app_label, ct.model)
            kwargs['instance_pk'] = instance.pk
        return kwargs

    def __init__(self, participant=None, **kwargs):
        if participant is not None:
            kwargs.update(self._init_with_participant(participant, **kwargs))
        kwargs.setdefault('username', None)
        kwargs.setdefault('fullname', None)
        kwargs.setdefault('email', None)
        kwargs.setdefault('content_type', None)
        kwargs.setdefault('instance_pk', None)
        kwargs.setdefault('role', None)
        kwargs.setdefault('contact_info', None)
        super(Participant, self).__init__(**kwargs)

    @property
    def is_sender(self):
        return bool(getattr(self, 'role', None) == 'from')

    @property
    def instance(self):
        if self.content_type and self.instance_pk:
            app_label, model = self.content_type.split('.', 1)
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model)
                model_class = ct.model_class()
                try:
                    return ct.get_object_for_this_type(pk=self.instance_pk)
                except model_class.DoesNotExist:
                    pass
            except ContentType.DoesNotExist:
                pass

class Message(Immutable):
    """
    Message parameters that are passed around within the pr_messaging app.
    """

    def __init__(self, message_type=None, context=None, sender=None,
                 recipients=None, **kwargs):
        kwargs['message_type'] = message_type
        kwargs['context'] = context or {}
        pkwds = {}
        pkwds['skip_instance_check'] = kwargs.pop('skip_instance_check', False)
        if kwargs.get('participants', None) is None:
            participants = [Participant(sender, role='from', **pkwds)]
            if 'recipient' in kwargs:
                participants.append(Participant(kwargs.pop('recipient'), role='to', **pkwds))
            for recipient in (recipients or []):
                participants.append(Participant(recipient, role='to', **pkwds))
            for recipient in kwargs.pop('to', []):
                participants.append(Participant(recipient, role='to', **pkwds))
            for recipient in kwargs.pop('cc', []):
                participants.append(Participant(recipient, role='cc', **pkwds))
            for recipient in kwargs.pop('bcc', []):
                participants.append(Participant(recipient, role='bcc', **pkwds))
            kwargs['participants'] = participants
        kwargs.setdefault('message_format', None)
        kwargs.setdefault('subject', None)
        kwargs.setdefault('body', None)
        super(Message, self).__init__(**kwargs)

    def sender(self):
        """Return the participant who is the sender of the message, or None."""
        try:
            return [p for p in self.participants if p.role == 'from'][0]
        except IndexError:
            return None

    def recipients(self):
        """Return all participants who are recipients."""
        return [p for p in self.participants if p.role in ('to', 'cc', 'bcc')]

    def split_by_recipient(self):
        """Split this message into new messages for each recipient."""
        new_messages = []
        for recipient in self.recipients():
            participants = [recipient]
            sender = self.sender()
            if sender:
                participants.insert(0, sender)
            new_message = self.updated(participants=participants)
            new_messages.append(new_message)
        return new_messages
