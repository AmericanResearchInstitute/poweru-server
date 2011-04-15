from django.core.management import call_command

def setup(machine):
    call_command('loaddata', 'precor_org_roles.json', verbosity=0, commit=False)
