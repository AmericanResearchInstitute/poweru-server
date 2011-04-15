import django.test
import manager
from xml.etree import cElementTree

class TestCase(django.test.TestCase):
    def setUp(self):
        self.manager = manager.Manager()
        self.manager.add_shipment_method('FedEx Express Saver', 'F14', True)
        self.manager.add_shipment_method('FedEx Standard', 'F06', True)

class TestSubmit(TestCase):
    def test_all(self):
        order = {    'first_name' : 'Test',
                                'last_name' : 'User',
                                'email' : 'test@user.com',
                                'phone' : '919-123-4567',
                                'label' : '123 Main St.',
                                'locality' : 'Raleigh',
                                'region' : 'NC',
                                'postal_code' : '27609',
                                'country' : 'US',
                                'shipment_method' : 'FedEx Express Saver',
                                'line_items' : [
                                                {'sku' : 'CCUPEN', 'quantity' : '2'},
                                                {'sku' : 'CCUPAD', 'quantity' : '1'}]
                            }
        order_id = manager.Manager().register_order(**order)

        ret = manager.Manager().flush()
        self.assertEquals(len(ret['failure']), 0)
        self.assertEquals(len(ret['success']), 1)
        
# vim:tabstop=4 shiftwidth=4 expandtab
