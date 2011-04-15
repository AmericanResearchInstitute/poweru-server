"""
Paypal module for use with ecommerce.merchant_services
"""

import urllib
from paypal_settings import settings
from datetime import datetime
from models import paypal_ec_token
from paypal_tools import api_tools
from exceptions import invalid_response_exception

class direct_payment(object, api_tools):
    """
    Communicate with Paypal, a particular merchant services provider.
    """

    def __init__(self, data, settings = settings()):
        """
        Constructor
        
        @param data   dictionary of transaction attribute values indexed by name
        @type data dict
        """

        self.data = data

        # Paypal requires a 4-digit year, which is unusual
        current_year = str(datetime.utcnow().year)
        ed = str(self.data['exp_date'])
        new_year = current_year[:2] + ed[2:]
            # That's right, I'm assuming that the expiration is within 100 years.
            # Youwannafightaboutit????
        if int(new_year) < int(current_year):
            new_year = str(int(current_year[:2]) + 1) + ed
        self.data['exp_date'] = ed[:2] + new_year

        # Enforce length limits as defined by Paypal
        self.data['invoice_number'] = self.data['invoice_number'][:127]
        self.data['address_label'] = self.data['address_label'][:100]
        self.data['first_name'] = self.data['first_name'][:25]
        self.data['last_name'] = self.data['last_name'][:25]
        self.data['country'] = self.data['country'][:2]
        self.data['state'] = self.data['state'][:40]
        self.data['city'] = self.data['city'][:40]
        self.data['zip'] = self.data['zip'][:20]

        self.settings = settings
    
    def translate(self, data):
        """
        Convert attribute names from our own schema to Paypal's.
        
        @param data   dictionary of attribute names and values that will be passed to the gateway
        @type data dict
        @return       dictionary of attribute names and values with Paypal-compatible names.
        @rtype dict
        """

        #: Paypal attribute names indexed by corresponding PR names.
        mapping = {
            'transaction_id' : 'TRANSACTIONID',
            'card_type' : 'CREDITCARDTYPE',
            'invoice_number' : 'INVNUM',
            'first_name' : 'FIRSTNAME',
            'address_label' : 'STREET',
            'country' : 'COUNTRYCODE',
            'last_name' : 'LASTNAME',
            'card_number' : 'ACCT',
            'sales_tax' : 'TAXAMT',
            'exp_date' : 'EXPDATE',
            'ip' : 'IPADDRESS',
            'state' : 'STATE',
            'amount' : 'AMT',
            'city' : 'CITY',
            'cvv2' : 'CVV2',
            'zip' : 'ZIP',
        }
        
        ret = {}
        for atr in data:
            d = data[atr]
            if d is not None:
                ret[mapping[atr]] = d
        return ret
        
    
    def charge(self):
        """
        stub that calls the right method
        """

        return self.DoDirectPayment()

    def credit(self):
        """
        stub that calls the right method
        """

        return self.RefundTransaction()

    def DoDirectPayment(self):
        """
        Execute a transaction.
        """

        # Translate attribute names to what Paypal wants to see.
        self.data = self.translate(self.data)
        # Add Paypal-specific transaction attributes.
        self.data.update({
                'PAYMENTACTION' : 'Sale',
                'METHOD' : 'DoDirectPayment',
        })

        url_data = urllib.urlencode(self.add_common_parameters(self.data))
        return self.gen_response(self.get_url(url_data))

    def RefundTransaction(self):
        """ returnd a transaction """

        self.data = self.translate(self.data)
        url_data = urllib.urlencode(
                self.add_common_parameters({
                    'TRANSACTIONID' : self.data['TRANSACTIONID'],
                    'REFUNDTYPE' : 'Partial',
                    'METHOD' : 'RefundTransaction',
                    'AMT' : self.data['AMT'],
        }))

        return self.gen_response(self.get_url(url_data))

class express_checkout(object, api_tools):
    """
    Use paypal's Express Checkout feature.
    """

    def __init__(self, settings = settings()):
        self.settings = settings
        self.credentials = self.add_common_parameters({})

    def get_token_url(self, amount):
        """
        Get the URL, including token, to use for accessing Paypal.
        
        @param amount     Amount of sale
        
        @return           URL
        """

        data = self.credentials.copy()
        data.update({
            'METHOD' : 'SetExpressCheckout',
            'RETURNURL' : self.settings.return_url,
            'CANCELURL' : self.settings.cancel_url,
            'AMT' : amount,
            'NOSHIPPING' : '1',
            })

        response = self.get_url(urllib.urlencode(data))
        if 'TOKEN' not in response:
            raise invalid_response_exception(str(response) + str(data))

        token = paypal_ec_token(token = response['TOKEN'], amount = amount,
                                time=datetime.utcnow())
        token.save()

        # the 'useraction=commit' makes the paypal site appear to complete the transaction with
        # something like a "Pay Now" button, instead of sending the user back to us to review
        # the details before submitting a payment
        return token.token, '%s&useraction=commit&token=%s' % (settings.express_checkout_url,
                                                               token.token)
  
# vim:tabstop=4 shiftwidth=4 expandtab
