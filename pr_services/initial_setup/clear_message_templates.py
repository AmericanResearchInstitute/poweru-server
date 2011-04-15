import pr_messaging

def setup(machine):
    pr_messaging.models.MessageTemplate.objects.all().delete()
    pr_messaging.models.MessageType.objects.all().delete()
    pr_messaging.models.MessageFormat.objects.all().delete()
