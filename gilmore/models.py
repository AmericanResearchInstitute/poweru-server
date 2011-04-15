from django.db import models
from pr_services import models as pr_models

class LineItem(pr_models.OwnedPRModel):
    sku = models.CharField(max_length=31)
    quantity = models.PositiveSmallIntegerField()
    order = pr_models.PRForeignKey('Order', related_name='line_items')

class Order(pr_models.OwnedPRModel):
    #: the User's last name / surname
    last_name = models.CharField(max_length=31)
    #: the User's first name / given name / Christian name
    first_name = models.CharField(max_length=31)
    email = models.EmailField()
    phone = models.CharField(max_length=31, null=True)
    #: country (two letter ISO code, e.g. us, fi, de, jp, cn)
    country = models.CharField(max_length=2)
    #: state in the US
    region = models.CharField(max_length=31)
    #: city in the US
    locality = models.CharField(max_length=31)
    #: zip code in the US
    postal_code = models.CharField(max_length=16)
    #: all Address lines above the locality but below a person's name
    label = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    sent = models.DateTimeField(null=True)
    confirmation_code = models.CharField(max_length=31, null=True)
    shipment_method = pr_models.PRForeignKey('ShipmentMethod', related_name='orders')

class ShipmentMethod(pr_models.OwnedPRModel):
    name = models.CharField(max_length=63, unique=True)
    code = models.CharField(max_length=16, unique=True)
    active = pr_models.PRBooleanField(default=True)

# vim:tabstop=4 shiftwidth=4 expandtab
