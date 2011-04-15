"""
Paypal module for use with ecommerce.merchant_services.
"""

import urllib
from exceptions import paypal_token_not_found_exception
from pr_logging import raw_response
from paypal_settings import settings
from models import paypal_ec_token
from paypal_tools import api_tools
import settings as project_settings

class express_checkout(object, api_tools):
    """
    Use Paypal's Express Checkout feature.
    """

    def __init__(self, settings = settings()):
        self.settings = settings
        self.credentials = self.add_common_parameters({})

    def complete(self, token):
        """
        Complete a sale.
        
        @param token  the string issued by paypal which identifies a transaction
        @type token str
        
        @return      dictionary containing transaction_id and result_message
        @rtype dict
        """

        try:
            token = paypal_ec_token.objects.get(token = token)
        except paypal_ec_token.DoesNotExist:
            raise paypal_token_not_found_exception

        data = self.credentials.copy()
        data.update({
            'METHOD' : 'GetExpressCheckoutDetails',
            'TOKEN' : token.token,
        })

        details = self.get_url( urllib.urlencode(data) )

        data = self.credentials.copy()
        data.update({
            'METHOD' : 'DoExpressCheckoutPayment',
            'TOKEN' : token.token,
            'PAYMENTACTION' : 'Sale',
            'PAYERID' : details['PAYERID'],
            'AMT' : token.amount,
        })
        
        rr = raw_response()
        payment = self.get_url( urllib.urlencode(data) )
        rr.text = str(payment)
        rr.enter()

        token.delete()

        context = { 'AMT' : payment['AMT'],
                    'FIRSTNAME' : details['FIRSTNAME'],
                    'LASTNAME' : details['LASTNAME'],
                    'ORDERTIME' : payment['ORDERTIME'],
                    'TRANSACTIONID' : payment['TRANSACTIONID'],
                    }

        return context
        
# vim:tabstop=4 shiftwidth=4 expandtab
