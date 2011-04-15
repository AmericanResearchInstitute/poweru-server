from django.core.management import call_command

def setup(machine):
    call_command('loaddata', 'precor_orgs.json', verbosity=0, commit=False)
