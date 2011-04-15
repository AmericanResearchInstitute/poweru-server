from django.db import models

class PRBooleanField(models.BooleanField):
    """
    We have our own custom BooleanField so that the values 'FALSE', 'True', 'false', '1', etc. are all interpreted as boolean values through the to_python magic
    """
    def to_python(self, value):
        if str(value).lower() in ['t', 'true', '1']:
            return True
        if str(value).lower() in ['f', 'false', '0']:
            return False
        return super(PRBooleanField, self).to_python(value)

class PRForeignKey(models.ForeignKey):
    def __init__(self, to, **kwargs):
        if kwargs.setdefault('null', False):
            kwargs['on_delete'] = models.SET_NULL
        else:
            kwargs['on_delete'] = models.PROTECT
        super(PRForeignKey, self).__init__(to, **kwargs)

class PROneToOneField(models.OneToOneField):
    def __init__(self, to, **kwargs):
        if kwargs.setdefault('null', False):
            kwargs['on_delete'] = models.SET_NULL
        else:
            kwargs['on_delete'] = models.PROTECT
        super(PROneToOneField, self).__init__(to, **kwargs)

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^pr_services\.fields\.PRBooleanField"])
add_introspection_rules([], ["^pr_services\.fields\.PRForeignKey"])
add_introspection_rules([], ["^pr_services\.fields\.PROneToOneField"])
