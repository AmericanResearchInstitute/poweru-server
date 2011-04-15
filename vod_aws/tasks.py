from celery.decorators import task
from celery.task.sets import subtask
from django.conf import settings
from django.core.files import File
import facade
import fastenc
import logging
import os
import tempfile
from vod_aws import awsutils
import urlparse
from pr_services import exceptions
import urllib

logger = logging.getLogger('vod_aws.tasks')

def s3_url_for_encoding_com(path, source=False):
    '''Create URLs for files in an Amazon S3 bucket for sending to encoding.com

    :param path: Path to file, with or without leading slash.
    :type path: str
    :param source: Whether the url is to be used by encoding.com as a source (if False, creates a destination url).
    :type source: bool
    '''
    params = {}
    if not source:
        params['canonical_id'] = settings.AWS_CANONICAL_USER_ID
    return urlparse.urlunparse((
        'http',
        '%s.s3.amazonaws.com' % (settings.AWS_STORAGE_BUCKET_NAME),
        path,
        None,
        urllib.urlencode(params),
        None))

@task(max_retries=5, ignore_result=True)
def queue_encoding(video_id, notify_url, **kwargs):
    """Queue encoding of a video in our Amazon S3 bucket

    Once the job is queued, a mediaid is returned for the entire job which is
    then stored on the Video object.

    :param video_id: the primary key for a :class:`vod_aws.models.Video` object
    :type video_id: integer
    :param notify_url: the URL encoding.com will use to notify us that the
        encoding is done
    :type notify_url: string
    """
    video = facade.models.Video.objects.get(pk=video_id)

    # give encoding.com permission to read the source video
    video.src_file.file.key.add_user_grant('READ', settings.AWS_ENCODING_OAI_S3_USER)

    # form the encoding.com request
    # video bitrates based on: http://adterrasperaspera.com/blog/2010/05/24/approximate-youtube-bitrates
    format_list = [
        fastenc.query.create_format_element(
            output='fl9',
            bitrate='256k',
            size='320x180',
            audio_codec='libfaac',
            destination=s3_url_for_encoding_com('video/%d.low.f4v' % video_id)),
        fastenc.query.create_format_element(
            output='fl9',
            bitrate='512k',
            size='640x360',
            audio_codec='libfaac',
            destination=s3_url_for_encoding_com('video/%d.medium.f4v' % video_id)),
        fastenc.query.create_format_element(
            output='fl9',
            bitrate='2048k',
            size='1280x720',
            audio_codec='libfaac',
            destination=s3_url_for_encoding_com('video/%d.high.f4v' % video_id)),
        fastenc.query.create_format_element(
            output='thumbnail',
            width='160',
            height='90',
            destination=s3_url_for_encoding_com('video/%d.thumbnail.jpg' % video.id))
    ]
    request = fastenc.actions.AddMedia(
        settings.ENCODING_USERID,
        settings.ENCODING_USERKEY,
        s3_url_for_encoding_com(video.src_file.name, source=True),
        notify_url,
        format_list=format_list)

    try:
        logger.info('sending AddMedia request to encoding.com for video(%d)' % video_id)
        response = request.send()
    except Exception, exc:
        queue_encoding.retry(args=[video_id, notify_url], exc=exc, kwargs=kwargs)

    mediaid = response.findtext('MediaID')
    if mediaid is not None:
        logger.info('queued encoding job for video(%d) with mediaid("%s")' % (video_id, mediaid))
        video.encoding_job_mediaid = mediaid
        video.save()
    else:
        # No MediaID back means an error occurred.
        queue_encoding.retry(args=[video_id, notify_url], exc=exc, kwargs=kwargs)

@task(max_retries=5, ignore_result=True)
def process_video_notification(encoding_job_mediaid, **kwargs):
    """Creates EncodedVideo objects and thumbnails based on results from encoding.com.

    This is a Celery task because we need to fetch some information from
    encoding.com to store in the EncodedVideo record.  This information is not
    provided by their notification to us that the encoding job is done.  In the
    event we cannot contact their web service right away, being able to use
    celery to retry the task is valuable.

    :param encoding_job_mediaid: the identifier for the encoding job we queued
        with encoding.com
    :type encoding_job_mediaid: string
    """
    video = facade.models.Video.objects.get(encoding_job_mediaid=encoding_job_mediaid)

    request = fastenc.actions.GetStatus(
        settings.ENCODING_USERID,
        settings.ENCODING_USERKEY,
        encoding_job_mediaid)
    try:
        logging.info('sending GetStatus request to encoding.com for video(%d)' % video.id)
        response = request.send()
    except Exception, exc:
        process_video_notification.retry(args=[encoding_job_mediaid], exc=exc, kwargs=kwargs)

    video.src_file.file.key.remove_user_grant('READ', settings.AWS_ENCODING_OAI_S3_USER)

    for format in response.findall('format'):
        destination = urlparse.urlsplit(format.findtext('destination')).path.lstrip('/')
        if format.findtext('output') == 'thumbnail':
            video.photo = destination
            video.save()
            # TODO: we do a read and a write to set the permissions here,
            # but since we know what permissions we want to end up with,
            # we should try to do it with one write. we should also try to
            # chown the file to ourselves
            video.photo.file.key.remove_user_grant('FULL_CONTROL', settings.AWS_ENCODING_OAI_S3_USER)
        else:
            encoded_video = facade.models.EncodedVideo.objects.create(
                video=video,
                output = format.findtext('output'),
                bitrate = format.findtext('bitrate'),
                size = format.findtext('size'),
                audio_codec = format.findtext('audio_codec'),
                video_codec = format.findtext('video_codec'),
                file = destination)
            # TODO: we do 2 reads and 2 writes to set the permissions here,
            # but since we know what permissions we want to end up with,
            # we should try to do it with one write. we should also try to
            # chown the file to ourselves
            encoded_video.file.file.key.remove_user_grant('FULL_CONTROL', settings.AWS_ENCODING_OAI_S3_USER)
            encoded_video.file.file.key.add_user_grant('READ', settings.AWS_CLOUDFRONT_OAI_S3_USER)
    if video.src_file.name:
        video.src_file.delete()
    video.is_ready = True
    video.save()
