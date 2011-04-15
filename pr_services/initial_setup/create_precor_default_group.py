import facade

def setup(machine):
    facade.models.Group.objects.create(name='Default', default=True)
