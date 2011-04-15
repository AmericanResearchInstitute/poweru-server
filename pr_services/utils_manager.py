from facade import models
import pr_services.exceptions as exceptions
from django.db.models.fields import FieldDoesNotExist
from pr_services.rpc.service import service_method
import logging
import time

class UtilsManager(object):
    """Utility methods usable through RPC."""
    logger = logging.getLogger('UtilsManager')

    @service_method
    def get_choices(self, model_name, attribute_name):
        """
        Fetch the list of valid values for a model's multiple-choice attribute

        :param model_name:     The name of the model to look in.
        :type model_name:      string
        :param attribute_name: The name of the attribute to query.
        :type attribute_name:  string
        :return:               A list of the valid choices (empty if it's not a multiple-choice attribute).
        :raises:               pr_services.exceptions.FieldNameNotFoundException if there is no model with the name specified or it doesn't contain the specified attribute.
        """

        try:
            model = getattr(models, model_name)
        except AttributeError:
            self.logger.debug("no model named '%s'" % model_name)
            time.sleep(1)
            raise exceptions.FieldNameNotFoundException("not found")

        try:
            field = model._meta.get_field_by_name(attribute_name)[0]
        except FieldDoesNotExist:
            self.logger.debug("model named '%s' has no field named '%s'" % (model_name, attribute_name))
            time.sleep(1)
            raise exceptions.FieldNameNotFoundException("not found")

        return [ c[0] for c in field.flatchoices ]
