"""
Product manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ProductManager(ObjectManager):
    """
    Manage Products in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'custom_actions' : 'get_many_to_many',
            'description' : 'get_general',
            'display_order' : 'get_general',
            'inventory' : 'get_inventory_from_product',
            'cost' : 'get_general',
            'name' : 'get_general',
            'price' : 'get_general',
            'sku' : 'get_general',
            'starting_quantity' : 'get_general',
            'training_units' : 'get_general',
        })
        self.setters.update({
            'description' : 'set_general',
            'display_order' : 'set_general',
            'cost' : 'set_general',
            'name' : 'set_general',
            'price' : 'set_general',
            'sku' : 'set_general',
            'starting_quantity' : 'set_general',
            'training_units' : 'set_general',
            'custom_actions' : 'set_many',
        })
        self.my_django_model = facade.models.Product

    @service_method
    def create(self, auth_token, sku, name, description, price, cost,
            optional_attributes=None):
        """
        Create a new Product
        
        @param sku                              SKU, up to 32 characters
        @param name                             name of the Product, up to 127 characters
        @param description                      description, text field
        @param price                            price in cents that we charge
        @param cost                             price in cents that it costs us to obtain this

        @return                                 a reference to the newly created Product
        """

        if not optional_attributes:
            optional_attributes = dict()

        blame = facade.managers.BlameManager().create(auth_token)
        p = self.my_django_model(sku=sku, name=name, description=description, price=price, cost=cost,
                blame=blame)
        if isinstance(optional_attributes, dict):
            p.save()
            facade.subsystems.Setter(auth_token, self, p, optional_attributes)
        p.save()
        self.authorizer.check_create_permissions(auth_token, p)
        return p

    @service_method
    def get_discounted_price(self, auth_token, product, promo_code):
        """
        Get the best discount currently available for a Product given a promo_code
        
        @param product    Foreign key for a Product
        @param promo_code Promotional code, not case sensitive
        
        @return           Discounted price, if any
        """

        p = self._find_by_id(product)
        self.authorizer.check_read_permissions(auth_token, p, ['price'])
        discount = p.product_discounts.filter(promo_code__iexact = promo_code, active = True).order_by('-discount_percentage')
        if discount:
            self.authorizer.check_read_permissions(auth_token, discount[0], ['discount_percentage'])
            return int(p.price * (1 - discount[0].discount_percentage / 100.))
        else:
            return None

# vim:tabstop=4 shiftwidth=4 expandtab
