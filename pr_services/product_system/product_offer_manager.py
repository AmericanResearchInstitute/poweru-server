"""
ProductOffer manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class ProductOfferManager(ObjectManager):
    """
    Manage ProductOffers in the Power Reg system

    <pre>
    ProductOffer attributes:
      description   Text Field, custom description for the product being offered
      product       Foreign Key for the product being offered
      price         Price in cents
      seller        Foreign Key for the user selling the product
    </pre>
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'description' : 'get_general',
            'price' : 'get_general',
            'product' : 'get_foreign_key',
            'seller' : 'get_foreign_key',
        })
        self.setters.update({
            'description' : 'set_general',
            'price' : 'set_general',
            'product' : 'set_foreign_key',
            'seller' : 'set_foreign_key',
        })
        self.my_django_model = facade.models.ProductOffer

    @service_method
    def create(self, auth_token, product, seller, price, description):
        """
        Create a new ProductOffer
        
        @param product        Foreign Key for a product
        @param seller         Foreign Key for the user who is a seller
        @param price          Price in cents
        @param description    Custom description of the product
        @return               a reference to the newly created ProductOffer
        """

        blame = facade.managers.BlameManager().create(auth_token)
        p = self.my_django_model(description = description, price = price, blame = blame)
        facade.subsystems.Setter(auth_token, self, p, {'product' : product, 'seller' : seller})
        p.save()
        self.authorizer.check_create_permissions(auth_token, p)
        return p

    @service_method
    def get_discounted_price(self, auth_token, product_offer, promo_code):
        """
        Get the best discount currently available for a ProductOffer given a promo_code
        
        @param product_offer  Foreign key for a ProductOffer
        @param promo_code     Promotional code, not case sensitive
        
        @return               Discounted price, if any
        """

        p = self._find_by_id(product_offer)
        self.authorizer.check_read_permissions(auth_token, p, ['price'])
        discount = p.product_discounts.filter(promo_code__iexact = promo_code, active = True).order_by('-discount_percentage')
        if discount:
            self.authorizer.check_read_permissions(auth_token, discount[0], ['discount_percentage'])
            return int(p.price * (1 - discount[0].discount_percentage / 100.))
        else:
            return None

# vim:tabstop=4 shiftwidth=4 expandtab
