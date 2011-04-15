import logging
from django.db.models import Q
import facade

logger = logging.getLogger('pr_services.handlers')

def pr_user_instance_requested(sender, **kwargs):
    logger.debug('pr_user_instance_requested sender=%r kwargs=%r', sender, kwargs)
    participant = kwargs.get('participant', None)
    if participant:
        User = facade.models.User
        try:
            if participant.email:
                return User.objects.get(Q(email=participant.email) |
                                        Q(email2=participant.email))
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            pass

def pr_user_contact_requested(sender, **kwargs):
    logger.debug('pr_user_contact_requested sender=%r kwargs=%r', sender, kwargs)
    participant = kwargs.get('participant', None)
    message = kwargs.get('message', None)
    if participant and message:
        instance = participant.instance
        if instance and getattr(instance, 'suppress_emails', False):
            return False
