from django.db import models

class paypal_ec_token(models.Model):
    """ Paypal Express Checkout token """
    amount = models.CharField(max_length = 15)
    token = models.CharField(max_length = 20)
    time = models.DateTimeField() #: timestamp -- these are only good for 3 hours

# vim:tabstop=4 shiftwidth=4 expandtab
