"""
Exceptions for Power Reg exam system.
"""

__docformat__ = "restructuredtext en"

# Django
from django.conf import settings

# PowerReg
from pr_services.pr_exceptions import PrException

class ExamSessionAlreadyFinishedException(PrException):
    """
    exception - exam_session already finished
    """
    error_code = 66
    error_msg = "exam_session has been previously finished"

class InvalidResponseException(PrException):
    """
    exception - invalid respone
    """
    error_code = 69
    error_msg = "invalid response"

class ExamResponseAlreadyReceivedException(PrException):
    """
    exception - response already received
    """
    error_code = 71
    error_msg = "a response to this question or rating has already been" + \
        " received"

class ExamSessionScoreAlreadyCalculatedException(PrException):
    """
    exception - exam session score has already been calculated
    """
    error_code = 89
    error_msg = "The exam_session score has already been calculated"

class ExamSessionNotFinishedException(PrException):
    """
    exception - exam_session not finished
    """
    error_code = 90
    error_msg = "exam_session has not been finished"

# vim:tabstop=4 shiftwidth=4 expandtab
