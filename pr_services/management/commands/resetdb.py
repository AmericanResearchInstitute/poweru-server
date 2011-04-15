from django.core.management import call_command
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    requires_model_validation = False

    def handle_noargs(self, **options):
        call_command('dropalltables')
        call_command('syncdb', **options)
        call_command('migrate')
