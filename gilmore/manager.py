from xml.etree import cElementTree
from xml.parsers.expat import ExpatError
import urllib
import urllib2
from datetime import datetime
from django.conf import settings
import models
import exceptions

class Manager(object):
    def add_shipment_method(self, name, code, active):
        """
        @param name     name
        @type  name     str
        @param code     A code assigned to this shipping method by Gilmore
        @type  code     str
        @param active   should this be useable for new orders?
        @type  active   bool
        """
        if models.ShipmentMethod.objects.filter(name=name).count() > 0 or models.ShipmentMethod.objects.filter(code=code).count() > 0:
            raise exceptions.ShipmentMethodExistsException
        models.ShipmentMethod.objects.create(name=name, code=code, active=active)

    def register_order(self, first_name, last_name, email, phone, country, region, locality, postal_code, label, shipment_method, line_items):
        """
        @param line_items   list of dictionaries, each representing a product. Each
                            has keys 'sku' and 'quantity'
        @type  line_items   list
        @return             order id
        """

        order = models.Order(first_name=first_name, last_name=last_name,
                email=email, phone=phone, country=country, region=region,
                locality=locality, postal_code=postal_code, label=label)
        try:
            order.shipment_method = models.ShipmentMethod.objects.get(name=shipment_method, active=True)
        except models.ShipmentMethod.DoesNotExist:
            raise exceptions.InvalidOrderException('shipment method %s not found' % (shipment_method))
        order.save()

        try:
            for item in line_items:
                models.LineItem.objects.create(sku=item['sku'], quantity=item['quantity'], order=order)
        except KeyError:
            raise exceptions.InvalidOrderException('each line item must include a sku and quantity')
        return order.id

    def build_xml(self, order):
        """
        Build an xml data structure to represent an order to Gilmore

        @param  order       order ID
        @type   order       string
        @return             XML structure as a string
        """


        root = cElementTree.Element('printorder')
        client = cElementTree.Element('client')
        root.append(client)
        name = cElementTree.Element('name')
        name.text = settings.GILMORE_CLIENT_NAME
        client.append(name)
        storepackorder = cElementTree.Element('storePackOrder')
        client.append(storepackorder)

        fullname = cElementTree.Element('fullName')
        fullname.text = '%s %s' % (order.first_name, order.last_name)
        label = order.label.split('\n', 1)
        street1 = cElementTree.Element('streetAddress_1')
        street1.text = label[0]
        street2 = cElementTree.Element('streetAddress_2')
        street2.text = label[1] if len(label) > 1 else ''
        city = cElementTree.Element('city')
        city.text = order.locality
        state = cElementTree.Element('state')
        state.text = order.region
        zip = cElementTree.Element('zip')
        zip.text = order.postal_code
        country = cElementTree.Element('country')
        country.text = order.country
        email = cElementTree.Element('email')
        email.text = order.email
        phone = cElementTree.Element('phone')
        phone.text = order.phone
        storepackorder.append(fullname)
        storepackorder.append(street1)
        storepackorder.append(street2)
        storepackorder.append(city)
        storepackorder.append(state)
        storepackorder.append(zip)
        storepackorder.append(country)
        storepackorder.append(phone)
        storepackorder.append(email)

        shipment_method = cElementTree.Element('shipmentMethod')
        shipment_method.text = order.shipment_method.code
        storepackorder.append(shipment_method)
        
        order_element = cElementTree.Element('orderId')
        order_element.text = '%s%s' % (settings.GILMORE_CLIENT_NAME, str(order.id))
        storepackorder.append(order_element)

        for line_item in order.line_items.all():
            package_item = cElementTree.Element('packageItem')
            sku = cElementTree.Element('sku')
            sku.text = line_item.sku
            package_item.append(sku)
            quantity = cElementTree.Element('quantity')
            quantity.text = str(line_item.quantity)
            package_item.append(quantity)
            storepackorder.append(package_item)

        return cElementTree.tostring(root, 'UTF-8')

    def send_order(self, order):
        """
        Send an order to Gilmore.

        @param order    Either an instance of models.Order, or the primary key
                        for one.
        """
        if not isinstance(order, models.Order):
            try:
                order = models.Order.objects.get(id=order)
            except models.Order.DoesNotExist:
                raise exceptions.OrderNotFoundException

        return_value = False
        post_data = {'xmlstr' : self.build_xml(order)}
        try:
            ret = urllib2.urlopen(settings.GILMORE_URL, urllib.urlencode(post_data))
            if ret.code == 200:
                body = ret.read()
                if body:
                    response_xml = cElementTree.fromstring(body)
                    if response_xml.find('message').text == 'success':
                        order.sent = datetime.utcnow().replace(microsecond=0)
                        order.confirmation_code = response_xml.find('confirmationCode').text
                        order.save()
                        return_value = True
        except urllib2.URLError:
            raise exceptions.UnableToConnectToGilmoreException()
        except ExpatError:
            raise exceptions.InvalidResponseException()
        return return_value

    def flush(self):
        """
        Find all orders that have not been submitted and attempt to submit them

        This should probably be run from a cron job every few minutes.  That
        cron job should write a PID file and check for its existance before
        running so we don't get two going at once. It would also be nice to
        make sure that PID file hasn't been around for too long, in case the
        process gets stuck or dies improperly.

        It is important to not run this method in a transaction. If some orders
        succeed, we don't want to revert them because something broke later on.

        @return a dictionary with two lists of order ids indexed as 'success'
                    and 'failure'.  You can guess what that means.
        """
        ret = {'success' : [], 'failure' : []}
        for order in models.Order.objects.filter(sent__isnull=True).select_related():
            if self.send_order(order):
                ret['success'].append(order.id)
            else:
                ret['failure'].append(order.id)
        return ret

# vim:tabstop=4 shiftwidth=4 expandtab
