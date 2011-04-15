"""
ProductDiscount manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ProductDiscountManager(ObjectManager):
    """ 
    Manage ProductDiscounts. Only one of product and product_offer should be defined.

    <pre>
    ProductDiscount attributes:
      discount_percentage   Integer from 0-100, inclusive
      product               Foreign Key for the product to which this applies
      product_offer         Foreign Key for the product_offer to which this applies
      promo_code            String, up to 15 characters, case insensitive
    </pre>
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'condition_test_collection' : 'get_many_to_many',
            'cumulative' : 'get_general',
            'currency' : 'get_general',
            'name' : 'get_general',
            'percentage' : 'get_general',
            'products' : 'get_many_to_many',
            'product_offers' : 'get_many_to_many',
            'promo_code' : 'get_general',
            'training_units' : 'get_general',
        })
        self.setters.update({
            'condition_test_collection' : 'set_many',
            'cumulative' : 'set_general',
            'currency' : 'set_general',
            'name' : 'set_general',
            'percentage' : 'set_general',
            'products' : 'set_many',
            'product_offers' : 'set_many',
            'promo_code' : 'set_general',
            'training_units' : 'set_general',
        })
        self.my_django_model = facade.models.ProductDiscount

    @service_method
    def create(self, auth_token, name, currency, training_units, percentage, cumulative, products, product_offers, promo_code=None, condition_test_collection=None):
        """
        Create a new ProductDiscount for each product and product_offer listed
        
        @param name                         up to 63 characters
        @param currency                     straight currencty value to deduct, in cents
        @param training_units               straight training_units value to deduct
        @param percentage                   Percentage discount, integer from 0-100 inclusive
        @param cumulative                   boolean to determine if this should be cumulative with other discounts
        @param products                     List of foreign keys for products
        @param product_offers               List of foreign keys for product_offers
        @param promo_code                   optional string up to 15 characters, case sensitive
        @param condition_test_collection    FK of a condition_test_collection, optional
        @return                             reference to new ProductDiscount
        """

        blame = facade.managers.BlameManager().create(auth_token)
        if condition_test_collection is not None:
            ctc_object = self._find_by_id(condition_test_collection, facade.models.ConditionTestCollection)
        else:
            ctc_object = None

        p = self.my_django_model(currency=currency, cumulative=cumulative,
                percentage=percentage, blame=blame, promo_code=promo_code,
                condition_test_collection=ctc_object, name=name)
        p.save()

        facade.subsystems.Setter(auth_token, self, p, {
                'products' : {'add' : products},
                'product_offers' : {'add' : product_offers},
        })

        p.save()
        self.authorizer.check_create_permissions(auth_token, p)

        return p

# vim:tabstop=4 shiftwidth=4 expandtab
