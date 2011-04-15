"""Database models for pr_messaging app."""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.template import Template

class MessageFormat(models.Model):
    """
    Message formats supported in the system.
    
    Each message format corresponds to a different messaging medium or
    protocol, such as:
        email
        email-html
        sms
        mms
        twitter
        ...
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=32, unique=True)
    description = models.TextField(blank=True, null=True)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.slug)

class MessageType(models.Model):
    """
    Each message type represents a particular named notification in the system.
    
    For example:
        user-registration
        status-change
        payment-received
        password-expired
        ...
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    enabled = models.BooleanField(default=True)

    # Does this message type support multiple recipients? If True, the 
    # corresponding template(s) will be rendered once for ALL recipients. If
    # False, the template(s) must be rendered once for EACH recipient.
    multiple_recipients = models.BooleanField(default=False)

    # FIXME: Does this type support aggregation of multiple signals?
    # for example, if a user gets added to three different groups all at once,
    # it would be a shame to send three emails. If multiple_contexts == True,
    # then context for each of the three signals will be combined and the
    # template will render one message saying "You've been added to these
    # groups: ..."
    #multiple_contexts = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.slug)

class MessageTemplate(models.Model):
    """
    A template for rendering messages for a given format and type...
    """

    message_type = models.ForeignKey(MessageType, related_name='message_templates')
    message_format = models.ForeignKey(MessageFormat, related_name='message_templates')

    subject = models.CharField(max_length=255)
    body = models.TextField()

    class Meta:
        unique_together = ('message_type', 'message_format')

    def __unicode__(self):
        return u'%s template for %s messages' % (self.message_format.name, self.message_type.name)

    def render(self, context):
        subject = Template(self.subject).render(context)
        body = Template(self.body).render(context)
        # Tries to render a plain text format as well for HTML emails.
        # FIXME: Should really find a more generic way to add attachments and
        # alternate content types.
        if 'email' in self.message_format.slug and 'html' in self.message_format.slug:
            try:
                mt = MessageTemplate.objects.get(message_format__slug='email',
                                                 message_type=self.message_type)
                plain_text_body = Template(mt.body).render(context)
            except MessageTemplate.DoesNotExist:
                pass
            else:
                return subject, plain_text_body, (None, body, 'text/html')
        return subject, body

class SentMessage(models.Model):
    """
    Records info about a message that was sent successfully.
    """

    message_template = models.ForeignKey(MessageTemplate, related_name='sent_messages')
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def sender(self):
        try:
            return self.participants.get(role='from')
        except SentMessageParticipant.DoesNotExist:
            return None
        except SentMessageParticipant.MultipleObjectsReturned:
            raise

    @property
    def recipients(self):
        return self.participants.filter(role__in=('to', 'cc', 'bcc')).all()

    def __unicode__(self):
        return u'%s @ %s' % (self.message_template, self.timestamp)

class SentMessageParticipant(models.Model):
    """
    Records a participant's info and role for a sent message.

    To add a reference to this model from either a recipient or sender model in
    your app, add a line like this to your model:

        sent_message_participants = generic.GenericRelation(
            SentMessageParticipant, object_id_field='participant_id')
    
    To then limit the results to messages where the model was only a sender or
    receiver:
    
        as_sender = obj.sent_message_participants.filter(role='from')
        as_receiver = obj.sent_message_participants.filter(role__in=('to','cc','bcc))

    """

    ROLE_CHOICES = [('From', 'from'), ('To', 'to'), ('CC', 'cc'), ('BCC', 'bcc')]

    sent_message = models.ForeignKey(SentMessage, related_name='participants')
    role = models.CharField(max_length=8, choices=ROLE_CHOICES)
    content_type = models.ForeignKey(ContentType, null=True, default=None)
    participant_id = models.PositiveIntegerField(null=True, default=None)
    participant_contact = models.CharField(max_length=255)
    participant = generic.GenericForeignKey('content_type', 'participant_id')

    def __unicode__(self):
        return u'%s: %s' % (self.role, self.participant_contact)

# Defer importing handlers until the end...
from . import handlers
