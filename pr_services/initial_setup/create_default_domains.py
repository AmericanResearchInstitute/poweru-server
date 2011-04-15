import facade

def setup(machine):
    facade.models.Domain.objects.create(name='local')
    facade.models.Domain.objects.create(name='LDAP')
