from celery.decorators import task
from datetime import datetime, timedelta
import facade

import settings
if 'ecommerce' in settings.INSTALLED_APPS:
    from ecommerce import paypal_tools

@task(ignore_result=True)
def cleanup_paypal_ec_tokens(*args, **kwargs):
    """Cleans up expired Paypal Express Checkout tokens."""
    if 'ecommerce' in settings.INSTALLED_APPS:
        paypal_tools.paypal_utils().cleanup_paypal_ec_tokens()


@task(ignore_result=True)
def expire_old_credentials(*args, **kwargs):
    """
    Finds Credentials with expiration in the past and set their status to
    'expired'.
    """
    facade.models.Credential.objects.filter(
        date_expires__lte=datetime.utcnow()).exclude(status='expired').update(
            status='expired')


@task(ignore_result=True)
def process_completed_sessions(*args, **kwargs):
    """
    Finds Sessions with end date + event.lag_time in the past, and sets their
    status to 'completed'.
    """
    right_now = datetime.utcnow()
    active_past_sessions = facade.models.Session.objects.filter(
        end__lt=right_now, status='active')
    for session in active_past_sessions:
        if (session.event.lag_time is None) or (
                session.end + session.event.lag_time < right_now):
            session.status = 'completed'
            session.save()


@task(ignore_result=True)
def process_session_reminders(*args, **kwargs):
    """
    This searches through the database, looking for sessions which
    require lead time notifications to be sent, sending emails
    as appropriate and logging its progress via the
    job, session_reminder_job, and session_reminder_item models
    """
    facade.managers.SessionManager()._process_session_reminders()


@task(ignore_result=True)
def remove_old_auth_tokens(*args, **kwargs):
    """
    Removes expired auth tokens and used single-use auth tokens from the
    database
    """
    facade.models.SingleUseAuthToken.objects.filter(used=True).delete()
    facade.models.AuthToken.objects.filter(
        time_of_expiration__lte=datetime.utcnow()).delete()
