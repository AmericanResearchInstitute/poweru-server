"""
ecommerce exceptions
"""

from pr_services.exceptions import PrException
import local_settings

class invalid_xml_response_exception(PrException):
    """
    Exception - Invalid XML response
    """

    error_code = 1000
    error_msg = "invalid XML response"

class connection_error_exception(PrException):
    """
    Exception - Invalid XML response
    """

    error_code = 1001
    error_msg = "error connecting to the merchant services gateway"

class transaction_failure_exception(PrException):
    """
    Exception - Invalid XML response
    """

    error_code = 1002
    error_msg = 'transaction failure'

    def __init__(self, error_message):
        self.error_msg = error_message

class transaction_denied_exception(PrException):
    """
    Exception - Transaction Denied exception
    """

    error_code = 1003
    error_msg = "transaction denied by merchant services provider"

class database_error_exception(PrException):
    """
    Exception - Database Error
    """

    error_code = 1004
    error_msg = 'database error'

    def __init__(self, error_message):
        self.error_msg = error_message

class invalid_input_exception(PrException):
    """
    Exception - invalid input
    """

    error_code = 1005
    error_msg = 'invalid input'

    def __init__(self, error_message):
        self.error_msg = error_message

class invalid_response_exception(PrException):
    """
    Exception - Invalid response
    """

    error_code = 1006
    error_msg = "invalid response from the merchant services gateway"

    def __init__(self, msg=''):
        if local_settings.DEBUG:
            self.error_msg = "invalid response from the merchant services gateway: %s" % (msg)

class must_use_txn_data_exception(PrException):
    """
    Exception - must use txn_data
    """

    error_code = 1007
    error_msg = "this type of transaction must use the txn_data class"

class paypal_token_not_found_exception(PrException):
    """
    Exception - Paypal token not found
    """

    error_code = 1008
    error_msg = "paypal token not found"

class action_not_supported_exception(PrException):
    """
    Exception - The requested action is not supported
    """

    error_code = 1009
    error_msg = "requested action is not supported"

# vim:tabstop=4 shiftwidth=4 expandtab
