"""
ProductClaim manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade
from pr_services import exceptions

class ProductClaimManager(ObjectManager):
    """
    Manage ProductClaims in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'product' : 'get_foreign_key',
            'purchase_order' : 'get_foreign_key',
            'quantity' : 'get_general',
            'price_paid' : 'get_general',
            'training_units_paid' : 'get_general',
            'discounts' : 'get_many_to_many',
            'assignments' : 'get_many_to_one',
        })
        self.setters.update({
            'product' : 'set_foreign_key',
            'purchase_order' : 'set_foreign_key',
            'quantity' : 'set_general',
        })
        self.my_django_model = facade.models.ProductClaim

    @service_method
    def create(self, auth_token, product, purchase_order, quantity):
        """
        Create a new Product
        
        @param product          PK of the product
        @param purchase_order   PK of the purchase_order
        @param quantity         Positive Integer

        @return                                 a reference to the newly created ProductClaim
        """
        blame = facade.managers.BlameManager().create(auth_token)
        product_object = self._find_by_id(product, facade.models.Product)
        purchase_order_object = self._find_by_id(purchase_order, facade.models.PurchaseOrder)
        pc = self.my_django_model(product=product_object, purchase_order=purchase_order_object, quantity=quantity, blame=blame)
        pc.save()
        pc.set_prices()
        pc.save()
        self.authorizer.check_create_permissions(auth_token, pc)
        if pc.quantity > 0:
            facade.models.ProductTransaction.objects.create(product=product_object, change=-quantity, blame=blame)

        return pc

    @service_method
    def update(self, auth_token, id, value_map):
        if 'quantity' in value_map:
            pc = self._find_by_id(id)
            if pc.quantity != value_map['quantity']:
                blame = facade.managers.BlameManager().create(auth_token)
                facade.models.ProductTransaction.objects.create(product=pc.product, change=(value_map['quantity'] - pc.quantity), blame=blame)
                
        pc = ObjectManager.update(auth_token, id, value_map)
        pc.set_prices()
        return pc

    @service_method
    def choose_assignments(self, auth_token, product_claim, assignments):
        product_claim_object = self._find_by_id(product_claim)
        if len(assignments) > product_claim_object.remaining_paid_assignments:
            raise exceptions.NotPaidException
        assignment_objects = facade.models.Assignment.objects.in_bulk(assignments)
        for assignment_id in assignment_objects:
            assignment = assignment_objects[assignment_id]
            assignment.product_claim = product_claim_object
            assignment.save()

# vim:tabstop=4 shiftwidth=4 expandtab
