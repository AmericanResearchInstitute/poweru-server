from django.http import HttpResponse, HttpResponseBadRequest
from xml.etree.ElementTree import fromstring, tostring
from xml.parsers.expat import ExpatError
import logging
import vod_aws.tasks

def video_notification(request):
    """Receive video completion notifications from encoding.com

    A URL pointing to this view should be sent to encoding.com with transcode
    requests so that the hit this page and trigger EncodedVideo model updates
    """
    logger = logging.getLogger('vod_aws.views.video_notification')

    # Only handle POST requests, otherwise just show a blank page
    if request.method == 'POST':
        try:
            result = fromstring(request.POST['xml'])
        except KeyError:
            logger.error('request POST contained no XML data')
            return HttpResponseBadRequest()
        except ExpatError, e:
            logger.error('request POST xml parse error: %s' % (e.message))
            return HttpResponseBadRequest()

        # At this point, we should have XML that looks like this:
        #=======================================================================
        # <result>
        #    <mediaid>[MediaID]</mediaid>
        #    <source>[SourceFile]</source>
        #    <status>[MediaStatus]</status>
        #    <description>[ ErrorDescription]</description> <!-- Only in case of Status = Error -->
        #    <format>
        #        <output>[OutputFormat]</output>
        #        <destination>[DestFile]</destination> <!-- Only in case of Status = Finished -->
        #        <status>[TaskStatus]</status>
        #        <description>[ErrorDescription]</description> <!-- Only in case of Status = Error -->
        #        <suggestion>[ErrorSuggestion]</suggestion> <!-- Only in case of Status = Error -->
        #    </format>
        #    <format>
        #        ...
        #    </format>
        # </result>
        #
        # Note the lowercase 'mediaid', instead of 'MediaID' as it is elsewhere
        #=======================================================================

        # TODO: Currently this only acts on videos for which we've been notified.
        #  Doing a batch "GetStatus" on the MediaID we've been told about as well as
        #  old jobs that (for whatever reason) we don't know about would be a good idea

        # status can be "Error" or "Finished"
        status = result.findtext('status')
        if status == 'Finished':
            mediaid = result.findtext('mediaid')
            logger.info('Encoding.com job with MediaID %s is finished.' % mediaid)
            vod_aws.tasks.process_video_notification.delay(mediaid)
        elif status == 'Error':
            # Error message is result.find('description').text
            # Log the XML to get more debugging from encoding.com
            logger.error('Encoding.com reported an error: "%s". Enable DEBUG logging for full XML.' % result.findtext('description'))
            logger.debug(tostring(result))
        else:
            logger.error('Unknown status %s from encoding.com. Enable DEBUG logging for full XML.' % status)
            logger.debug(tostring(result))

    return HttpResponse()
