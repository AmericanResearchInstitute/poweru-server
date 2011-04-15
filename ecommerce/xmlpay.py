#!/usr/bin/python

from xml.etree import cElementTree

class ObjectWithTextSubElements:
    def _create_sub_elements_with_text(self, parent, elements):
        """
        Take a dictionary of text items indexed by element name, create an
        xml.etree.cElementTree.Element object for each one, and append them to
        the parent.

        @param parent   instance of xml.etree.cElementTree.Element to which the
                        new Element objects should be appended
        @type  parent   Element
        @param elements dictionary of text items indexed by element name.  Any
                        items which are not text will be safely ignored.
        @type  elements dict
        """

        for element in elements:
            if isinstance(elements[element], str) or isinstance(elements[element], unicode):
                sub_element = cElementTree.Element(element)
                sub_element.text = elements[element]
                parent.append(sub_element)

class XMLPayRequest(object):
    def __init__(self, request_data, request_auth):
        """
        Represents an XMLPayRequest structure as defined by the XMLPay spec

        @param request_data     instance of RequestData
        @type  request_data     RequestData
        @param request_auth     instance of RequestAuth
        @type  request_auth     RequestAuth
        """

        self.element = cElementTree.Element('XMLPayRequest')
        self.element.append(request_data.element)
        self.element.append(request_auth.element)

    def get_xml(self):
        """
        @return string of UTF-8 encoded XML representing this object
        """

        return cElementTree.tostring(self.element, encoding='UTF-8')

class RequestData(object, ObjectWithTextSubElements):
    def __init__(self, Vendor, Partner, transactions):
        """
        Represents a RequestData structure as defined by the XMLPay spec

        @param Vendor       From the XMLPay spec: 'Identifies the merchant of
                            record for the transaction within the target payment
                            processing network.'
        @type  Vendor       string
        @param Partner      From the XMLPay spec: 'Identified the submitting
                            party'
        @type  Partner      string
        @param transactions list of Transaction objects
        @type  transactions list
        """

        self.element = cElementTree.Element('RequestData')
        self.element.append(cElementTree.Element('Transactions'))
        self._create_sub_elements_with_text(self.element, locals())

        for transaction in transactions:
            self.element.find('Transactions').append(transaction.element)

class RequestAuth(object, ObjectWithTextSubElements):
    def __init__(self, User, Password):
        """
        Represents a RequestAuth and UserPass structure as defined by the
        XMLPay spec.  We do not support Signature authentication, which is why
        both structures are here in one object.

        @param User     username
        @type  User     string
        @param Password password
        @type  Password string
        """

        params = locals()
        userpass = cElementTree.Element('UserPass')
        self._create_sub_elements_with_text(userpass, params)

        self.element = cElementTree.Element('RequestAuth')
        self.element.append(userpass)
        
class Transaction(object):
    def __init__(self, transaction_type, id=None, custref=None):
        """
        Represents a financial transaction as defined by the XMLPay spec

        @param transaction_type     instance of Sale or Authorization
        @param id                   Optional merchant-generated string that identifies the
                                    transaction.  If provided, it will be in the matching
                                    TransactionResult.  Must be unique
        @type  id                   string
        @param custref              Optional merhcant-generated string that identifies the
                                    customer.  If provided, it will be in the matching
                                    TransactionResult
        @type  custref              string
        """

        attributes = locals()
        for attr in attributes.keys():
            if type(attributes[attr]) != str:
                del attributes[attr]
        
        self.element = cElementTree.Element('Transaction', attributes)
        self.element.append(transaction_type.element)
    
class Authorization(object):
    def __init__(self, paydata):
        """
        Represents an Authorization structure as defined by the XMLPay spec

        @param paydata  instance of PayData
        @type  paydata  PayData
        """

        self.element = cElementTree.Element('Authorization')
        self.element.append(paydata.element)
    
class Sale(object):
    def __init__(self, paydata):
        """
        Represents a Sale structure as defined by the XMLPay spec

        @param paydata  instance of PayData
        @type  paydata  PayData
        """

        self.element = cElementTree.Element('Sale')
        self.element.append(paydata.element)

class PayData(object):
    def __init__(self, invoice=None, tender=None):
        """
        Represents a PayData structure as defined by XMLPay spec, which
        is a means of representing a payment against an invoice

        @param invoice  instance of Invoice
        @type  invoice  Invoice
        @param tender   instance of some structure that is a valid subelement
                        of 'Tender'
        """

        self.element = cElementTree.Element('PayData')
        if tender != None:
            tender_container = cElementTree.Element('Tender')
            tender_container.append(tender.element)
            self.element.append(tender_container)
        if invoice !=None:
            self.element.append(invoice.element)

class Invoice(object, ObjectWithTextSubElements):
    def __init__(self, TotalAmt, TaxAmt, CustIP, InvNum=None):
        """
        Represents an Invoice.

        @param TotalAmt     total amount to be charged
        @type  TotalAmt     string
        @param TaxAmt       amount of tax to be charged
        @type  TaxAmt       string
        @param CustIP       customer's IP address
        @type  CustIP       string
        @param InvNum       optional invoice number, but must be unique if
                            provided
        @type  InvNum       string
        """

        self.element = cElementTree.Element('Invoice')
        self._create_sub_elements_with_text(self.element, locals())

class Card(object, ObjectWithTextSubElements):
    def __init__(self, CardType, CardNum, ExpDate, CVNum, NameOnCard):
        """
        Represents a credit card.

        @param CardType     Visa, Amex, Discover, etc
        @type  CardType     string
        @param CardNum      number on the card
        @type  CardNum      string
        @param ExpDate      expiration date as YYYYMM
        @type  ExpDate      string
        @param CVNum        CVV2 number on the back of the card
        @type  CVNum        string
        @param NameOnCard   name on the card
        @type  NameOnCard   string
        """

        self.element = cElementTree.Element('Card')
        self._create_sub_elements_with_text(self.element, locals())

# vim:tabstop=4 shiftwidth=4 expandtab
