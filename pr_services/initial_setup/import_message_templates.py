from django.conf import settings
from django.template.loader import find_template_loader, make_origin, TemplateDoesNotExist
import pr_messaging

def find_template_source(name, dirs=None):
    """Custom version of find_template_source for Django >= 1.3, since
    find_template now always returns a compiled Template instance."""
    loaders = []
    for loader_name in settings.TEMPLATE_LOADERS:
        loader = find_template_loader(loader_name)
        if loader is not None:
            loaders.append(loader)
    for loader in loaders:
        try:
            source, display_name = loader.load_template_source(name, dirs)
            return (source, make_origin(display_name, loader, name, dirs))
        except TemplateDoesNotExist:
            pass
    raise TemplateDoesNotExist(name)

def setup(machine):
    pr_messaging.models.MessageFormat.objects.create(slug='email', name='Email')
    message_types = [
        ('log-message', 'Log Message'),
        #('assignment-late-notice', 'Assignment Late Notice'),
        #('assignment-pre-reminder', 'Assignment Pre-Reminder'),
        #('assignment-reminder', 'Assignment Reminder'),
        #('assignment-confirmation', 'Assignment Confirmation'),
        #('session-reminder', 'Session Reminder'),
        #('payment-confirmation', 'Payment Confirmation'),
        ('initial-password', 'Initial Password'),
        ('user-confirmation', 'User Confirmation'),
        ('password-reset', 'Password Reset'),
    ]
    for slug, name in message_types:
        pr_messaging.models.MessageType.objects.create(slug=slug, name=name)

    # Now load templates (from files for now)
    for mf in pr_messaging.models.MessageFormat.objects.filter(enabled=True):
        for mt in pr_messaging.models.MessageType.objects.filter(enabled=True):
            subject_tpl_name = '/'.join(['pr_messaging', mf.slug, mt.slug, 'subject.txt'])
            body_tpl_name = '/'.join(['pr_messaging', mf.slug, mt.slug, 'body.txt'])
            subject_tpl = find_template_source(subject_tpl_name)[0]
            body_tpl = find_template_source(body_tpl_name)[0]
            pr_messaging.models.MessageTemplate.objects.create(message_type=mt, message_format=mf, subject=subject_tpl, body=body_tpl)
