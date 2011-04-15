# Unit tests for the ecommerce application

import django.test
from datetime import datetime, timedelta
from merchant_services import txn_data, process_txn
from paypal import direct_payment
import time
import models
import paypal_tools
import xmlpay
from xml.dom import minidom
from xml.parsers import expat
import payflowpro
import payflowpro_settings
import e_settings

class test_payflowpro(django.test.TestCase):
    def setUp(self):
        self.t = txn_data('Visa', '4111111111111111', '1010', '100', str(time.time()), 'Gift Card', 'Recipient', '170 Southport Dr. Suite 400', 'Morrisville', 'NC',
            '27650', 'US', '204.16.138.148', '001')
        if payflowpro_settings.PWD:
            self.is_configured = True
        else:
            self.is_configured = False

    def test_charge(self):
        if self.is_configured:
            p = payflowpro.DirectPayment(self.t.get_dict()).charge()
            self.assertTrue(p['result_message'] in ['APPROVED', 'Approved', 'Success'])

class test_merchant_services(django.test.TestCase):
    def setUp(self):
        if e_settings.ms_provider == 'payflowpro':
            self.t = txn_data('Visa', '4111111111111111', '1010', '100', str(time.time()), 'Gift Card', 'Recipient', '170 Southport Dr. Suite 400', 'Morrisville', 'NC',
                '27650', 'US', '204.16.138.148', '001')
        else:
            # This data is for an American Express gift card that no longer has any value. As such, the name and address shouldn't have any bearing on
            # the approval decision.
            self.t = txn_data('Amex', '379014099768149', '1010', '100', str(time.time()), 'Gift Card', 'Recipient', '170 Southport Dr. Suite 400',
                'Morrisville', 'NC', '27650', 'US', '204.16.138.148', '4434')

    def test_charge_and_credit(self):
        p = process_txn(self.t).charge()
        self.assertTrue(p['result_message'] in ['APPROVED', 'Success', 'Approved'])
        if 'transaction_id' in p:
            self.t.transaction_id = p['transaction_id']
        if e_settings.ms_provider not in ['payflowpro']:
            p = process_txn(self.t).credit()
            self.assertTrue(p['result_message'] in ['APPROVED', 'Success', 'Approved'])

class test_paypal(django.test.TestCase):
    def setUp(self):
        # This data is for an American Express gift card that no longer has any value. As such, the name and address shouldn't have any bearing on the
        # approval decision.
        self.t = txn_data('Amex', '379014099768149', '1010', '100', str(time.time()), 'Gift Card', 'Recipient', '170 Southport Dr. Suite 400',
            'Morrisville', 'NC', '27650', 'US', '204.16.138.148', '4434')
        self.p = direct_payment(self.t.get_dict()).charge()

    def test_charge(self):
        self.assertEquals('result_message' in self.p, True)
        self.assertEquals('transaction_id' in self.p, True)

    def test_refund(self):
        self.t.cvv2 = None
        self.t.transaction_id = self.p['transaction_id']
        r = direct_payment(self.t.get_dict()).credit()
        self.assertEquals('result_message' in r, True)
        self.assertEquals('transaction_id' in r, True)

class test_paypal_utils(django.test.TestCase):
    def setUp(self):
        self.pu = paypal_tools.paypal_utils()
        
    def test_cleanup_paypal_ec_tokens(self):
        # make some Paypal express checkout tokens in the db
        ec_tokens = [models.paypal_ec_token(amount='$100.00', token='1',
                         time=(datetime.utcnow() - timedelta(hours=4))),
                     models.paypal_ec_token(amount='$110.00', token='2',
                         time=(datetime.utcnow() - timedelta(hours=3, minutes=30))),
                     models.paypal_ec_token(amount='$120.00', token='3',
                         time=(datetime.utcnow() - timedelta(hours=3))),
                     models.paypal_ec_token(amount='$130.00', token='4',
                         time=(datetime.utcnow() - timedelta(hours=2, minutes=30))),
                     models.paypal_ec_token(amount='$140.00', token='5',
                         time=(datetime.utcnow() - timedelta(hours=1))),
                     models.paypal_ec_token(amount='$150.00', token='6',
                         time=datetime.utcnow())]
        
        for ec_token in ec_tokens:
            ec_token.save()
    
        self.pu.cleanup_paypal_ec_tokens()
        self.assertEquals(models.paypal_ec_token.objects.count(), 3)
        self.assertEquals(models.paypal_ec_token.objects.filter(token='4').count(), 1)
        self.assertEquals(models.paypal_ec_token.objects.filter(token='5').count(), 1)
        self.assertEquals(models.paypal_ec_token.objects.filter(token='6').count(), 1)

class test_xmlpay(django.test.TestCase):
    def test_structures(self):
        c = xmlpay.Card('Amex', '379014099768149', '1010', '4434', 'Gift Card Recipient')
        i = xmlpay.Invoice('99.95', '0', str(time.time()))
        p = xmlpay.PayData(i, c)
        s = xmlpay.Sale(p)
        t = xmlpay.Transaction(s)
        rd = xmlpay.RequestData('Paypal', 'ARI', [t])
        ra = xmlpay.RequestAuth('ari', 'secretpassword')
        pr = xmlpay.XMLPayRequest(rd, ra)

        xml = pr.get_xml()

        # Now we will try to parse the XML using a different library
        try:
            parsed = minidom.parseString(xml)
        except expat.ExpatError:
            raise AssertionError('the XML that was generated could not be parsed by minidom')

# vim:tabstop=4 shiftwidth=4 expandtab
