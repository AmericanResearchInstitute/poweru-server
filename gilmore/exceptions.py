from pr_services.exceptions import PrException

class InvalidOrderException(PrException):
    """
    Exception - Invalid order
    """

    error_code = 2000
    error_msg = 'invalid order'

    def __init__(self, message):
        self.error_msg = message

class ShipmentMethodExistsException(PrException):
    """
    Exception - Shipment method already exists
    """

    error_code = 2001
    error_msg = 'shipment method already exists'

class UnableToConnectToGilmoreException(PrException):
    """
    Exception - We were unable to make a connection to Gilmore
    """

    error_code = 2002
    error_msg = 'unable to connect to Gilmore'

class InvalidResponseException(PrException):
    """
    Exception - We received an invalid response from Gilmore
    """

    error_code = 2003
    error_msg = 'invalid response from Gilmore'

# vim:tabstop=4 shiftwidth=4 expandtab
