"""
PurchaseOrder manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade
from pr_messaging import send_message

class PurchaseOrderManager(ObjectManager):
    """
    Manage PurchaseOrders in the Power Reg system
    
    <pre>
    purchase_order attributes:
    organization                   foreign Key for a organization with which
                              this object is associated. Only one of
                              organization and user should be defined.
    user                      foreign Key for a user with which this
                              object is associated. Only one of organization
                              and user should be defined.
    products                  array of product foreign keys which are for sale directly by us.
                              If you want to add these, you must specify a quantity. This is done
                              with a normal update() call using 'add', but each item in the list
                              indexed as 'add' will itself be a struct. That struct will have the
                              product's foreign key indexed as 'id', and quantity indexed as
                              'quantity'. If you want to change quantity later, you must remove
                              the product completely, and add it back with the new quantity. Don't
                              worry; this will not affect discount codes which have been applied.

                              Here's an example:
                              create(auth_token, t_units, t_units_price,
                                    {'products' : {'add' : [{'id' : 1, 'quantity' : 2}]}})
    product_offers            Works just like 'products', described above
    training_units_purchased  Integer number of training units being purchased
    training_units_price      Total price for the training units, measured in cents.
    expiration                ISO-8601 string representing the date and time after which
                              this PO is expired.
    active                    boolean value representing active status
    total                     derrived integer value. Do not request this unless you
                              really want it. This may cause performance problems in
                              bulk requests.
    </pre>
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        #: dictionary of attribute names and the functions used to get them
        self.getters.update({
            'expiration' : 'get_time',
            'is_paid' : 'get_is_paid_from_purchase_order',
            'organization' : 'get_foreign_key',
            'payments' : 'get_many_to_many',
            'product_claims' : 'get_many_to_one',
            'product_discounts' : 'get_many_to_many',
            'product_offers' : 'get_many_to_many',
            'products' : 'get_many_to_many',
            'promo_code' : 'get_general',
            'total_price' : 'get_general',
            'total_training_units' : 'get_general',
            'training_units_price' : 'get_general',
            'training_units_purchased' : 'get_general',
            'user' : 'get_foreign_key',
        })
        #: dictionary of attribute names and the functions used to set them
        self.setters.update({
            'expiration' : 'set_time',
            'organization' : 'set_foreign_key',
            'promo_code' : 'set_general',
            'user' : 'set_foreign_key',
            'training_units_purchased' : 'set_general',
            'training_units_price' : 'set_general',
        }) 
        self.my_django_model = facade.models.PurchaseOrder

    @service_method
    def create(self, auth_token, optional_parameters=None):
        """
        Create a new PurchaseOrder
        
        @param optional_parameters  dictionary of optional parameters indexed by
                                    parameter name: user, organization, expiration, training_units_purchased, training_units_price
        @return                     reference to a new purchase order
        """

        if optional_parameters is None:
            optional_parameters = {}

        p = self.my_django_model()
        p.blame = facade.managers.BlameManager().create(auth_token)
        p.user = p.blame.user
        p.owner = p.blame.user
        p.save() # We need to get a primary key before establishing many-to-many relationships
        if optional_parameters:
            facade.subsystems.Setter(auth_token, self, p, optional_parameters)
            p.save()
        self.authorizer.check_create_permissions(auth_token, p)

        for claim in p.product_claims.all():
            claim.set_prices()

        return p

    @service_method
    def update(self, auth_token, id, value_map):
        po = super(PurchaseOrderManager, self).update(auth_token, id, value_map)
        self.refresh_prices(auth_token, po)
        return po

    @service_method
    def refresh_discounts(self, auth_token, purchase_order):
        """
        """
        po = self._find_by_id(purchase_order)
        for claim in po.product_claim.object.all():
            claim.set_prices(True)
            self.authorizer.check_update_permissions(auth_token, claim, {'price_paid' : 0})
        return po

    @service_method
    def retrieve_receipt(self, auth_token, purchase_order_id):
        """
        Returns the text of the payment confirmation email for a given purchase order.
        
        @param auth_token
        @type auth_token pr_services.models.AuthToken
        @param purchase_order_id the primary key of the purchase order in question
        @type purchase_order_id int
        
        @returns payment validation email text based on the purchase order and its payments
        @rtype string
        """

        self.authorizer.check_arbitrary_permissions(auth_token, 'regenerate_payment_confirmations')
        
        po = self._find_by_id(purchase_order_id)
        template_context = po.get_template_context()
        # FIXME: this should return a recepit email preview when we have the new notification system
        # NOTE: this is documented above to return a string, but was actually returning a dict before it was stubbed out, and the tests expect a dict return!
        return { 'subject' : 'fake', 'body' : 'fake', 'html_body' : 'fake' }
    
    @service_method
    def resend_receipt(self, auth_token, purchase_order_id):
        """
        Send a payment confirmation email to a purchase order's associated user.
        
        @param auth_token
        @type auth_token pr_services.models.AuthToken
        @param purchase_order_id the primary key of the purchase order
        @type purchase_order_id int
        """

        self.authorizer.check_arbitrary_permissions(auth_token, 'resend_payment_confirmations')
        
        po = self._find_by_id(purchase_order_id)
        template_context = po.get_template_context()
        send_message(message_type='payment-confirmation',
                     context=template_context,
                     recipients=po.user)
        

# vim:tabstop=4 shiftwidth=4 expandtab
