"""
Payment manager class

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from pr_services import exceptions
from pr_services import pr_time
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade
from pr_messaging import send_message

# Only import ecommerce if this project is going to use it
import settings
if 'ecommerce' in settings.INSTALLED_APPS:
    from ecommerce.merchant_services import txn_data, process_txn
    from ecommerce.paypal import express_checkout

class PaymentManager(ObjectManager):
    """
    Manage Payments in the Power Reg system.
    
    <pre>
    payment attributes:
      purchase_order        Foreign Key for a purchase order
      card_type             One of: Visa, MasterCard, Discover, Amex
      card_number           Credit Card number
      exp_date              Expiration Date as four integers MMYY
      amount                Amount in cents
      invoice_number        Invoice Number
      first_name            First name on the card
      last_name             Last name on the card
      address_label         Address label for the card
      city                  City for the card
      state                 State for the card
      zip                   Zip Code for the card
      country               2-letter country code as defined in ISO-3166
      sales_tax             Sales tax in cents
      cvv2                  CVV2 Value, up to 4 digits. This does not get saved.
      refunds               List of structs with values for 'amount' and 'date'
    </pre>
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'refunds' : 'get_refunds_from_payment',
            'card_type' : 'get_general',
            'exp_date' : 'get_general',
            'amount' : 'get_general',
            'first_name' : 'get_general',
            'last_name' : 'get_general',
            'city' : 'get_general',
            'state' : 'get_general',
            'zip' : 'get_general',
            'country' : 'get_general',
            'sales_tax' : 'get_general',
            'transaction_id' : 'get_general',
            'invoice_number' : 'get_general',
            'result_message' : 'get_general',
            'purchase_order' : 'get_foreign_key',
            'date' : 'get_date_from_blame',
        })
        #: don't allow anything to be set, since a Payment is immutable
        #: after its creation
        self.setters.update({
            'refunds' : 'set_forbidden',
            'card_type' : 'set_forbidden',
            'exp_date' : 'set_forbidden',
            'amount' : 'set_forbidden',
            'first_name' : 'set_forbidden',
            'last_name' : 'set_forbidden',
            'city' : 'set_forbidden',
            'state' : 'set_forbidden',
            'zip' : 'set_forbidden',
            'country' : 'set_forbidden',
            'sales_tax' : 'set_forbidden',
            'transaction_id' : 'set_forbidden',
            'invoice_number' : 'set_forbidden',
            'result_message' : 'set_forbidden',
            'purchase_order' : 'set_forbidden',
            'date' : 'set_forbidden',
        })
        self.my_django_model = facade.models.Payment
        #: a list of methods that should be called before the
        #: processing of a Payment.  These methods should all
        #: take the Payment object as their first argument.
        self.my_pre_transaction_hooks = [self._is_po_already_paid]
        #: a list of methods that should be called after the
        #: successful processing of a Payment.  These methods should all
        #: take the Payment object as their first argument.
        self.my_post_transaction_hooks = [self._send_payment_confirmation]

    @service_method
    def create(self, auth_token, po, card_type, card_number, exp_date, amount,
            invoice_number, first_name, last_name, address_label, city, state,
            zip, country, cvv2, optional_parameters=None):
        """
        Create a Payment
        
        @param po                     Foreign Key for a purchase order
        @param card_type              One of: Visa, MasterCard, Discover, Amex
        @param card_number            Credit Card number
        @param exp_date               Expiration Date as four integers MMYY
        @param amount                 Amount in cents
        @param invoice_number         Invoice Number
        @param first_name             First name on the card
        @param last_name              Last name on the card
        @param address_label          Address label for the card
        @param city                   City for the card
        @param state                  State for the card
        @param zip                    Zip Code for the card
        @param country                2-letter country code as defined in ISO-3166
        @param cvv2                   CVV2 value.
        @param optional_parameters    sales_tax
        
        @return                       Reference to newly created Payment
        """

        if optional_parameters is None:
            optional_parameters = {}

        ip = auth_token.ip

        sales_tax = optional_parameters['sales_tax'] if 'sales_tax' in optional_parameters else 0

        local_po = self._find_by_id(po, facade.models.PurchaseOrder)
        # Run the list of pre-transaction hooks
        for transaction_hook in self.my_pre_transaction_hooks:
            transaction_hook(local_po)
        t = txn_data(card_type, card_number, exp_date, amount, invoice_number,
                first_name, last_name, address_label, city, state, zip,
                country, ip, cvv2, sales_tax)
        blame = facade.managers.BlameManager().create(auth_token)

        r = process_txn(t).charge()

        p = self.my_django_model(amount = amount, transaction_id = r['transaction_id'],
                purchase_order = local_po, card_number = card_number[-4:],
                result_message = r['result_message'], blame = blame,
                card_type = card_type, exp_date = exp_date, invoice_number = invoice_number,
                first_name = first_name, last_name = last_name, address_label = address_label,
                city = city, state = state, zip = zip, country = country, sales_tax = sales_tax)

        p.save()
        # Run the list of post transaction hooks
        for transaction_hook in self.my_post_transaction_hooks:
            transaction_hook(local_po)
        return p

    @service_method
    def refund(self, auth_token, payment, amount, card_number=None):
        """
        Make a refund
        
        @param payment      Primary Key for a Payment
        @param amount       Amount in cents
        @param card_number  Card number, only required for certain merchant service providers
        
        @return             Sucessfully refunded amount
        """

        p = self._find_by_id(payment)
        if card_number != None:
            p.card_number = card_number

        ip = auth_token.ip

        blame = facade.managers.BlameManager().create(auth_token)

        r = facade.models.Refund(payment = p, blame = blame, amount = amount)

        self.authorizer.check_create_permissions(auth_token, r)

        t = txn_data(card_type = p.card_type, card_number = p.card_number, exp_date = p.exp_date,
                amount = amount, invoice_number = p.invoice_number, first_name = p.first_name,
                last_name = p.last_name, address_label = p.address_label, city = p.city,
                state = p.state, zip = p.zip, country = p.country, ip = ip, sales_tax = p.sales_tax,
                transaction_id = p.transaction_id)

        credit = process_txn(t).credit()
        r.result_message = credit['result_message']
        r.transaction_id = credit['transaction_id']

        r.save()

        return r.amount

    @service_method
    def express_checkout(self, auth_token, po, amount):
        """
        Begin Paypal's Express Checkout process. No further calls are necessary
        for the Payment to be completed.
        
        @param po                 Foreign Key for a purchase order
        @param amount             Amount in cents
        
        @return    a URL which will take the user to Paypal's website to complete the transaction
        """

        if not str(amount).isdigit():
            raise exceptions.InvalidAmountException()
        po = self._find_by_id(po, purchase_order)
        for transaction_hook in self.my_pre_transaction_hooks:
            transaction_hook(po)    

        x = str(amount)
        while len(x) < 3:
            x = '0' + x
        amount = x[:-2] + '.' + x[-2:]

        token, url = express_checkout().get_token_url(amount)

        blame = facade.managers.BlameManager().create(auth_token)

        pt = paypal_ec_token(purchase_order = po, token = token, blame = blame)
        pt.save()

        return url

    def _complete_express_checkout(self, token, amount, transaction_id):
        """
        This gets called by the ecommerce app to complete a transaction
        
        @param token              String containing unique identifier from Paypal
        @param amount             Amount of transaction, in traditional decimal notation
        @param transaction_id     Transaction ID as given by Paypal
        """

        amount = int(str(amount).replace('.', ''))
        try:
            pt = paypal_ec_token.objects.get(token = token)
        except paypal_ec_token.DoesNotExist:
            raise exceptions.ExpressCheckoutTokenNotFoundException()
        except AssertionError:
            raise exceptions.ExpressCheckoutTokenNotFoundException()

        user = pt.blame.user

        p = self.my_django_model(amount = amount, transaction_id = transaction_id,
                purchase_order = pt.purchase_order, card_number = '', result_message = '',
                blame = pt.blame, card_type = '', exp_date = '', invoice_number = '',
                first_name = user.first_name, last_name = user.last_name,
                address_label = '', city = '', state = '', zip = '', sales_tax = 0)

        p.save()
        # Run the list of transaction hooks
        for transaction_hook in self.my_post_transaction_hooks:
            transaction_hook(pt.purchase_order)
        pt.delete()

    def _is_po_already_paid(self, po):
        """
        Raise an exception if the PO is already paid, otherwise return silently.
        """

        if po.is_paid:
            raise exceptions.PurchaseOrderAlreadyPaidException()

    def _send_payment_confirmation(self, po):
        """
        Send a payment confirmation to the user associated with the purchase
        order that the Payment was for, if the purchase order was associated
        with a user and not an organization.

        @param po purchase order in question
        """

        send_message(message_type='payment-confirmation',
                     context={'purchase_order': po},
                     recipient=po.user)
        

# vim:tabstop=4 shiftwidth=4 expandtab
