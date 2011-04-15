import urllib
from exceptions import invalid_response_exception, connection_error_exception, transaction_failure_exception, transaction_denied_exception, action_not_supported_exception
import xmlpay
from xml.etree import cElementTree
from xml.parsers.expat import ExpatError
import payflowpro_settings
from pr_logging import raw_response
from datetime import datetime

class PayFlowProTransaction:
    def _issue_request(self, xml):
        """
        This is a common method that can be used to submit a request in XML
        form to the payflowpro server

        @param xml  XML data structure expected by paypal's server
        @type  xml  string
        """
        rr = raw_response()
        try:
            response = urllib.urlopen(self.settings.URL, xml)
        except IOError:
            raise connection_error_exception

        rr.text = response.read()
        rr.enter()

        return self._parse_response(rr.text)

    def _handle_result_code(self, result_code):
        """
        Interpret a result code and act accordingly

        @param result_code  result code received from payflowpro server
        @type  result_code  int
        """
        result_code = int(result_code)

        if result_code == 0:
            pass #this means approved
        elif result_code == 1:
            raise transaction_failure_exception('authentication failed to the merchant services gateway')
        elif result_code == 4:
            raise transaction_failure_exception('invalid currency amount format.  Please indicate currency in cents')
        elif result_code == 12:
            raise transaction_denied_exception
        else:
            raise transaction_failure_exception('transaction failed')

        
class DirectPayment(object, PayFlowProTransaction):
    def __init__(self, data, settings = payflowpro_settings):
        """
        Constructor.

        @param data     A dictionary of data values output by merchant_services.txn_data
        @type  data     dict
        @param settings Any object that defines the attributes of
                        payflowpro_settings.py.example.  This defaults to
                        payflowpro_settings.py
        """

        self.data = data
        self.data['name'] = '%s %s' % (data['first_name'], data['last_name'])
        self.settings = settings
        self._mangle_data()

    def charge(self):
        """
        Charge a credit card.
        """
        return self._do_direct_payment()

    def credit(self):
        """
        Credit a credit card.
        """
        raise action_not_suppored_exception

    def _mangle_data(self):
        """
        Change the data in whatever way is necessary to please Paypal
        """

        # Payflow requires expiration date as YYYYMM
        current_year = str(datetime.utcnow().year)
        exp_month = self.data['exp_date'][:2]
        exp_year = self.data['exp_date'][2:]
        if int(exp_year) < int(current_year[2:]):
            exp_year = '%s%s' % (str(int(current_year[:2]) + 1), exp_year)
        else:
            exp_year = '%s%s' % (current_year[:2], exp_year)
        self.data['exp_date'] = '%s%s' % (exp_year, exp_month)

    def _do_direct_payment(self):
        """
        Run the transaction using Paypal's Direct Payment feature.
        """

        card = xmlpay.Card(self.data['card_type'], self.data['card_number'],
                self.data['exp_date'], self.data['cvv2'], self.data['name'])
        invoice = xmlpay.Invoice(self.data['amount'], self.data['sales_tax'],
                self.data['ip'], self.data['invoice_number'])
        pay_data = xmlpay.PayData(invoice, card)
        sale = xmlpay.Sale(pay_data)
        transaction = xmlpay.Transaction(sale)
        request_auth = xmlpay.RequestAuth(self.settings.USER, self.settings.PWD)
        request_data = xmlpay.RequestData(self.settings.VENDOR,
                self.settings.PARTNER, [transaction])
        xml_pay_request = xmlpay.XMLPayRequest(request_data, request_auth)

        return self._issue_request(xml_pay_request.get_xml())

    def _parse_response(self, response_text):
        """
        Take the XML received from paypal and make sense of it.

        @return Dictionary including 'result_message' and 'transaction_id'
        """
        try:
            response = cElementTree.fromstring(response_text)

            transaction_result = response.find('ResponseData').find('TransactionResults').find('TransactionResult')

            result_code = int(transaction_result.find('Result').text)
            self._handle_result_code(result_code)

            ret = { 'result_message' : transaction_result.find('Message').text,
                    'transaction_id' : transaction_result.find('PNRef').text }
        except (ExpatError, AttributeError):
            raise invalid_response_exception

        return ret

# vim:tabstop=4 shiftwidth=4 expandtab
