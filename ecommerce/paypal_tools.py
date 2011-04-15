"""
Paypal module for use with ecommerce.merchant_services

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2008 American Research Institute, Inc.
"""

import cgi
import logging
import urllib
from exceptions import connection_error_exception, transaction_failure_exception, invalid_response_exception
from pr_logging import raw_response
import models
from datetime import datetime, timedelta
from paypal_settings import settings

_logger = logging.getLogger('ecommerce.paypal_tools')

class api_tools:
    def add_common_parameters(self, data):
        """
        Accept a dictionary of parameter values indexed by name that are about to be send to paypal as a request,
        and add certain common parameters such as authentication credentials.

        @param data     dictionary of parameter values indexed by name
        @type data      dict
        @return         dictionary provided as 'data' with the addition of authorization credentials and 'VERSION'
        @rtype          dict

        """

        # See if we have a signature provided in the settings, and if so, make sure we do not also have a certificate
        if hasattr(self.settings, 'signature') and self.settings.signature and not (hasattr(self.settings, 'cert_file') or hasattr(self.settings, 'key_file')):
            data.update({'SIGNATURE' : self.settings.signature})

        data.update({
                'USER' : self.settings.user_id,
                'PWD' : self.settings.password,
                'VERSION' : '3.2',
        })
        return data

    def get_url(self, url_data):
        """
        Process an HTTP GET request given the full URL including XML
        and throw the response into a database ASAP in case something
        goes wrong during processing.
        
        @param url_data   The url-encoded data string
        @type url_data str
        @return           dictionary of response values indexed by name
        @rtype dict
        """

        log_prefix = u'api_tools.get_url(): '

        # Let's do this before the transaction just in case it causes trouble.
        rr = raw_response()

        # If we are using certificate authentication, this is where the magic happens
        if hasattr(settings, 'cert_file') and hasattr(settings, 'key_file') and settings.cert_file and settings.key_file:
            cert_args = {   'cert_file' : settings.cert_file,
                            'key_file' : settings.key_file, }
        else:
            cert_args = {}

        try:
            f = urllib.FancyURLopener(**cert_args).open(self.settings.url, url_data)
        except IOError, ioe:
            _logger.error(log_prefix + (u'IOError: [%s]' % unicode(ioe)))
            raise connection_error_exception

        # Throw this stuff into a database ASAP in case something goes wrong.
        rr.text = f.read()
        rr.enter()

        try:
            response = cgi.parse_qs(rr.text, strict_parsing = True)
        except ValueError, ve:
            _logger.error(log_prefix + (u'ValueError [%s]' % unicode(ve)))
         
            raise invalid_response_exception

        for key in response.keys():
            response[key] = response[key][0]

        return response

    def untranslate(self, data):
        """
        Convert attribute names from Paypal's naming scheme to our own.
        
        @param data   dictionary of parameter names and values returned in a transaction response.
        @type data dict

        @rtype dict
        """

        mapping = {
            'REFUNDTRANSACTIONID' : 'transaction_id',
            'TRANSACTIONID' : 'transaction_id',
            'ACK' : 'result_message',
        }

        ret = {}
        for atr in mapping:
            if atr in data:
                ret[mapping[atr]] = data[atr]
        return ret

    def handle_errors(self, r_dict):
        """
        Check the response for error conditions, and raise an exception if one is found.
        
        @param r_dict     dictionary of response values indexed by name
        @type r_dict dict
        """

        # Make sure this exists before accessing it.
        if 'ACK' not in r_dict:
            # FIXME: put some more information in the exception raised if reasonable
            raise invalid_response_exception

        # See if we failed
        if r_dict['ACK'] in set(['Failure', 'FailureWithWarning', 'Warning']):
            keys = r_dict.keys()
            error_messages = []

            # There may be more than error message, but their keys all start with the same string
            for key in keys:
                if key.upper().startswith('L_LONGMESSAGE'):
                    error_messages.append(r_dict[key])

            error = ''
            for message in error_messages:
                if len(error):
                    error += ' '
                error += message
            raise transaction_failure_exception(error)

        # Since we didn't fail, make sure we got a transaction_id
        if 'TRANSACTIONID' not in r_dict and 'REFUNDTRANSACTIONID' not in r_dict:
            # FIXME: put some more information in the exception if possible
            raise invalid_response_exception

    def gen_response(self, r_dict):
        """
        Take the data returned by Paypal and cook it in whatever way is necessary.
        """

        self.handle_errors(r_dict)
        return self.untranslate(r_dict)

class paypal_utils(object):
    """
    miscellaneous Paypal-related utilities that don't fit anywhere else
    """

    def __init__(self):
        pass

    def cleanup_paypal_ec_tokens(self):        
        """
        Search the database for stored Paypal express Checkout tokens, deleting
        ones older than 3 hours.
        """

        expired_ec_tokens = models.paypal_ec_token.objects.filter(
            time__lte = (datetime.utcnow()-timedelta(hours=3)))
        expired_ec_tokens.delete()
       
# vim:tabstop=4 shiftwidth=4 expandtab
