"""
@author Randy Barlow <rbarlow@americanri.com>
"""

import base64
import settings
import urllib
import urllib2
import xml.dom.minidom
import exceptions
from pr_services.rpc.service import service_method
    
class ReportGenerator(object):
    """
    This class acts as an interface between the front end and
    the Pentaho reporting suite.  It handles permissions and then
    fetches the report for the front end.
    """

    def __init__(self):
        """ constructor """

        pass

    @service_method
    def get_reports(self, auth_token):
        """
        This method can be used by the front end to fetch a list of reports available from pentaho.
        
        @param auth_token         The authentication token of the requesting user
        @type auth_token models.auth_token
        @return  dictionary whose keys are the report names and whose values are dictionaries
                 of default and required parameters.
        @rtype dict
        """
        
        return settings.PENTAHO_REPORTS

    @service_method
    def fetch_xml_report(self, auth_token, report_type, report_parameters=None):
        """
        This method can be used by the front end to fetch a report from
        Pentaho in an XML format.
        
        @param auth_token         The authentication token of the requesting user
        @type auth_token models.auth_token
        @param report_type        A string identifying the type of the report.  This
                                  report type must be found in the settings.PENTAHO_REPORTS
                                  dictionary.
        @type report_type unicode or str
        @param report_parameters  A dictionary of parameters and their values to be
                                  passed to the report.
        @type report_parameters dict
        @return the response from the Pentaho server
        @rtype str
        
        @raises InvalidReportTypeException
        @raises RequiredParameterMissingException
        @raises UnableToConnectToReportingServerException
        @raises XMLReportFailedException
        """

        if report_parameters is None:
            report_parameters = {}

        facade.subsystems.Authorizer().check_arbitrary_permissions(auth_token, 'read_reports')
        # This is needed for our Pentaho 2.0 setup but not for the previous
        # Pentaho 1.8 one.
        if not report_parameters.has_key('emailAddress'):
            report_parameters['emailAddress'] = 'empty'
        # Make sure that the requested report is one we are configured for
        if report_type not in settings.PENTAHO_REPORTS:
            raise exceptions.InvalidReportTypeException(report_type)
        # start building the GET parameters that we will pass
        report_settings = settings.PENTAHO_REPORTS[report_type]['default_parameters']
        # make sure the required parameters are present
        for required_parameter in settings.PENTAHO_REPORTS[report_type]['required_parameters']:
            if required_parameter not in report_parameters:
                raise exceptions.RequiredReportParameterMissingException(required_parameter)
        # add the report_parameters to the GET request
        for key in report_parameters.keys():
            report_settings[key] = report_parameters[key]
        pentaho_path = settings.PENTAHO_PATH+'?&'+urllib.urlencode(report_settings) # build the url
        url_to_fetch = 'http://'+settings.PENTAHO_HOST+pentaho_path # build the uri
        req = urllib2.Request(url_to_fetch)
        # Set up basic HTTP authentication for the request
        base64string = base64.encodestring('%s:%s' % (settings.PENTAHO_USERNAME,
                settings.PENTAHO_PASSWORD))[:-1]
        authheader =  "Basic %s" % base64string
        req.add_header("Authorization", authheader)
        try:
            # Fetch the result and store it
            url_client = urllib2.urlopen(req)
            result = url_client.read().strip()
        except urllib2.URLError: # We can't connect to the server
            raise exceptions.UnableToConnectToReportingServerException()
        # If the url_client has been set we want to close the connection, else we want to do nothing
        finally:
            try:
                if url_client:
                    url_client.close()
            except:
                pass

        try:
            dom = xml.dom.minidom.parseString(result)
        except:
            raise exceptions.XMLReportFailedException(result)
        else:
            if dom.getElementsByTagName('SOAP-ENV:Fault'):
                raise exceptions.XMLReportFailedException(result)
            
        return result

    @service_method
    def email_pdf_report(self, auth_token, email_address, report_type, report_parameters=None):
        """
        This method can be used by the front end to email a report from pentaho in PDF format.
        
        @param auth_token         The authentication token of the requesting user
        @type auth_token models.auth_token
        @param email_address email address to send the report to
        @type email_address str
        @param report_type   A string identifying the type of the report.  This report type
                             must be found in the settings.PENTAHO_REPORTS dictionary.
        @type report_type str
        @param report_parameters  A dictionary of parameters and their values to be passed to the report.
        @type report_parameters dict
        @return None
        
        @raises exceptions.InvalidReportTypeException
        @raises exceptions.RequiredParameterMissingException
        @raises exceptions.UnableToConnectToReportingServerExceptiona
        @raises exceptions.UnableToSendEmailReportException
        """
        
        if report_parameters is None:
            report_parameters = {}
        
        report_parameters['type'] = 'email'
        report_parameters['emailAddress'] = email_address
        try:
            result = self.fetch_xml_report(auth_token, report_type, report_parameters)
        except exceptions.XMLReportFailedException, x:
            if hasattr(x, 'details') and x.details.has_key('pentaho_result'):
                raise exceptions.UnableToSendEmailReportException(x.details['pentaho_result'])
            else:
                raise exceptions.UnableToSendEmailReportException()
        
        # If the result is invalid XML or contains a SOAP-ENV:Fault element, an error has occurred.
        try:
            dom = xml.dom.minidom.parseString(result)
        except:
            raise exceptions.UnableToSendEmailReportException(result)
        else:
            if dom.getElementsByTagName('SOAP-ENV:Fault'):
                raise exceptions.UnableToSendEmailReportException(result)

# vim:tabstop=4 shiftwidth=4 expandtab
