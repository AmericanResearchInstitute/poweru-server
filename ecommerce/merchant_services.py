"""
Merchant Services framework

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2008 American Research Institute, Inc.
"""

from exceptions import invalid_input_exception, must_use_txn_data_exception
import e_settings
from virtual_merchant import virtual_merchant
import paypal
import payflowpro
import time

class txn_data(object):
    """
    This class stores all of the data necessary to execute a merchant
    services transaction.  It is here so that validation and conversion may
    be done before going ahead.
    """
    __slots__ = [
        'card_type',
        'card_number',
        'exp_date',
        'amount',
        'invoice_number',
        'first_name',
        'last_name',
        'address_label',
        'city',
        'state',
        'country',
        'zip',
        'sales_tax',
        'cvv2',
        'ip',
        'transaction_id',
    ]

    def __init__(self, card_type, card_number, exp_date, amount, invoice_number, first_name, last_name, address_label, city, state, zip, country, ip, cvv2 = None,
            sales_tax = 0, transaction_id = None):
        card_type = card_type.lower()

        # Validation
        if card_type not in set(['visa', 'mastercard', 'discover', 'amex']):
            raise invalid_input_exception("Card type must be one of Discover, MasterCard, Visa, Amex")
        if len(exp_date) != 4 or not str(exp_date).isdigit():
            raise invalid_input_exception("Expiration date must be 4 digits with no spaces or punctuation.")

        l = locals()

        # Require certain fields
        for atr in ['card_type', 'card_number', 'exp_date', 'amount', 'invoice_number', 'first_name', 'last_name', 'address_label', 'city', 'state', 'zip', 'country', 
                'sales_tax', 'ip']:
            if atr not in l:
                raise invalid_input_exception("Missing parameter %s" % (atr))
        for atr in l:
            if atr in self.__slots__:
                setattr(self, atr, l[atr])
    
    def get_dict(self):
        """
        Get attributes in dictionary form
        
        @return   Dictionary of attribute values indexed by name
        """

        ret = {}
        for atr in self.__slots__:
            if hasattr(self, atr):
                ret[atr] = getattr(self, atr)
        ret['amount'] = self.from_cents(ret['amount'])
        ret['sales_tax'] = self.from_cents(ret['sales_tax'])
        return ret

    def from_cents(self, cents):
        """
        Convert an integer representing cents to a string representing
        dollars, or some other denomination with a decimal.
        
        @param cents  integer representing some number of cents in a currency
        """

        x = str(cents)
        while len(x) < 3:
            x = '0' + x
        return x[:-2] + '.' + x[-2:]


class process_txn:
    """
    class to process a transaction
    """

    def __init__(self, data):
        """
        constructor
        
        @param data   instance of class txn_data
        """

        self.data = data 
        providers = {
            'paypal' : paypal.direct_payment,
            'payflowpro' : payflowpro.DirectPayment,
            'virtual_merchant' : virtual_merchant,
        }
        self.ms_provider = providers[e_settings.ms_provider]

    def charge(self):
        """
        charge a credit card
        """

        if not isinstance(self.data, txn_data):
            raise must_use_txn_data_exception

        if e_settings.DEMO_MODE:
            return {'result_message' : 'Approved',
                    'transaction_id' : str(time.time() / 10) }
        
        return self.ms_provider(self.data.get_dict()).charge()

    def credit(self):
        """
        credit a credit card (refund)
        """

        if e_settings.DEMO_MODE:
            return {'result_message' : 'Approved',
                    'transaction_id' : str(time.time() / 10) }

        return self.ms_provider(self.data.get_dict()).credit()
    
# vim:tabstop=4 shiftwidth=4 expandtab
