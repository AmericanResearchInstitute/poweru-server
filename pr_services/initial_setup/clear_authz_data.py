import facade

def setup(machine):
    facade.models.ACMethodCall.objects.all().delete()
    facade.models.ACL.objects.all().delete()
    facade.models.Role.objects.all().delete()
    facade.models.ACCheckMethod.objects.all().delete()
