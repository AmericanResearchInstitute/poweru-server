"""
Virtual Merchant module for use with ecommerce.merchant_services
"""

from xml.dom.minidom import Document, parseString
from xml.parsers.expat import ExpatError
import urllib
from exceptions import invalid_xml_response_exception, connection_error_exception, transaction_failure_exception, transaction_denied_exception
from vm_settings import vm_settings
from pr_logging import raw_response

class virtual_merchant:
    """
    Communicate with Virtual Merchant, a particular merchant services provider
    """

    def __init__(self, data, settings = vm_settings()):
        """
        constructor
        
        @param data   Dictionary of transaction attribute values indexed by name
        @type data dict
        """

        self.data = data
        if 'address_label' in self.data:
            # VM has a 20 character limit on this field
            self.data['address_label'] = data['address_label'][:20]
        self.settings = settings

    def to_xml_doc(self, data):
        """
        Convert a dictionary to XML.
        
        @param data   dictionary of transaction parameter names and values
        @type data dict
        @return       instance of xml.dom.minidom.Document
        @rtype xml.dom.minidom.Document
        """

        d = Document()
        txn = d.createElement('txn')
        d.appendChild(txn)
        for atr in data:
            if data[atr]:
                buf = d.createElement(atr)
                txn.appendChild(buf)
                text = d.createTextNode(str(data[atr]))
                buf.appendChild(text)
        return d

    def untranslate(self, data):
        """
        Convert attribute names from Virtual Merchant's naming scheme to our own.
        
        @param data   Dictionary of parameter names and values returned in a transaction response.
        @type data dict
        @return dictionary with names translated for known fields
        @rtype dict
        """

        mapping = {
            'ssl_result' : 'result',
            'ssl_result_message' : 'result_message',
            'ssl_card_number' : 'card_number',
            'ssl_exp_date' : 'exp_date',
            'ssl_amount' : 'amount',
            'ssl_txn_id' : 'transaction_id',
            'ssl_approval_code' : 'approval_code',
            'ssl_avs_response' : 'avs_response',
        }

        ret = {}
        for atr in mapping:
            ret[mapping[atr]] = data[atr]
        return ret
    
    def translate(self, data):
        """
        Convert attribute names from our own schema to Virtual Merchant's
        
        @param data  dictionary of attribute names and values that will be passed to the gateway in XML
        @type data dict
        @return dictionary of attribute names and values with VM-compatible names.
        @rtype dict
        """

        #: Virtual Merchant attribute names indexed by corresponding PowerReg names.
        mapping = {
            'card_number' : 'ssl_card_number',
            'exp_date' : 'ssl_exp_date',
            'amount' : 'ssl_amount',
            'invoice_number' : 'ssl_invoice_number',
            'first_name' : 'ssl_first_name',
            'last_name' : 'ssl_last_name',
            'address_label' : 'ssl_avs_address',
            'city' : 'ssl_city',
            'state' : 'ssl_state',
            'zip' : 'ssl_avs_zip',
            'sales_tax' : 'ssl_salestax',
            'cvv2' : 'ssl_cvv2cvc2',
        }
        
        ret = {}
        for atr in mapping:
            ret[mapping[atr]] = data[atr]
        return ret
        
    def charge(self):
        """
        stub that calls execute with the right type
        """
        return self.execute('ccsale')

    def credit(self):
        """
        stub that calls execute with the right type
        """

        return self.execute('cccredit')

    def execute(self, type):
        """
        execute a transaction
        
        @param type   One of 'ccsale', 'cccredit'
        @type type str
        """

        self.data = self.translate(self.data) # Translate attribute names to what VM wants to see

        cvv2_use_map = {'ccsale' : '1',
                        'cccredit' : '0', }

        # Add VM-specific transaction attributes
        self.data.update({
                'ssl_transaction_type' : type,
                'ssl_merchant_id' : self.settings.merchant_id,
                'ssl_user_id' : self.settings.user_id,
                'ssl_pin' : self.settings.pin,
                'ssl_cvv2cvc2_indicator' : cvv2_use_map[type], # Assume that we have a CVV2 value and wish to use it.
        })

        if self.settings.debug:
            self.data.update({'ssl_test_mode' : 'TRUE'})
        xml_doc = self.to_xml_doc(self.data)
        return self.gen_response( self.get_url(xml_doc) )

    def gen_response(self, xml_response):
        """
        Convert an instance of xml.dom.minidom.Document to a dictionary.

        @param xml_response XML document to convert
        @type xml_response xml.dom.minidom.Document
        @return dictionary representing the XML document
        @rtype dict
        """

        ret = {}
        txn = xml_response.firstChild
        for node in txn.childNodes:
            if hasattr(node.firstChild, 'data'):
                ret[node.nodeName] = node.firstChild.data
        # This will raise an exception if an error message was received from VM
        self.handle_errors(ret)
        return self.untranslate(ret)

    def get_url(self, xml_doc):
        """
        GET the full url including xml, and throw the response into a
        database ASAP in case something goes wrong during processing.
        
        @param xml_doc    instance of xml.dom.minidom.Document
        @type xml_doc xml.dom.minidom.Document
        @return   dictionary of response values indexed by name
        @rtype dict
        """

        xml = xml_doc.toxml()
        # VM doesn't accept the standard XML meta tag, so we must perform foolishness to remove it.
        p = urllib.urlencode({'xmldata' : xml[xml.index('>') + 1:]})

        rr = raw_response() # Lets do this before the transaction just in case it causes trouble

        try:
            f = urllib.urlopen(self.settings.vm_url + '?%s' % p)
        except IOError:
            raise connection_error_exception

        # Throw this stuff into a database ASAP in case something goes wrong
        rr.text = f.read()
        rr.enter()

        try:
            response = parseString(rr.text)
        except ExpatError:
            raise invalid_xml_response_exception

        return response
    
    def handle_errors(self, response_dict):
        """
        Check the response for error conditions, and raise an exception if one is found.
        
        @param response_dict   Dictionary of response values indexed by name
        @type response_dict dict
        """

        if 'errorMessage' in response_dict:
            raise transaction_failure_exception(response_dict['errorMessage'])
        elif 'ssl_result' not in response_dict or response_dict['ssl_result'] != '0':
            raise transaction_denied_exception

# vim:tabstop=4 shiftwidth=4 expandtab
