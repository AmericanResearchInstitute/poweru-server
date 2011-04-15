'''Amazon Web Services helpers'''

from django.conf import settings
from M2Crypto import EVP
import base64
import boto.cloudfront
import boto.cloudfront.object
import boto.s3.bucket
import boto.s3.connection
import boto.s3.key
import facade
import logging
import os
import time
import urllib
import urlparse

try:
    import json
except ImportError:
    import simplejson as json

logger = logging.getLogger('vod.awsutils')

#===============================================================================
# Connection Helpers
#===============================================================================

class CloudFrontConnection(boto.cloudfront.CloudFrontConnection):
    '''Helper class to construct a CloudFront Connection with no args'''
    def __init__(self):
        super(CloudFrontConnection, self).__init__(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY) 

class S3Connection(boto.s3.connection.S3Connection):
    '''Helper class to construct an S3 Connection with no args'''
    def __init__(self, **kwargs):
        super(S3Connection, self).__init__(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, **kwargs)

    def get_my_bucket(self, validate=False):
        '''Get my bucket! Handily retrieves the bucket defined in settings.'''
        # validate=True will trigger a connection to AWS, which we generally
        # don't want
        return self.get_bucket(settings.AWS_STORAGE_BUCKET_NAME, validate=validate)

#===============================================================================
# CloudFront Helpers
#===============================================================================

# S3 Buckets can be related to both a Distribution and a
# StreamingDistribution, so it's useful to have both object types

class CloudFrontObject(boto.s3.key.Key):
    '''A boto CloudFront "Object" replacement

    This doesn't use bucket.distribution, because boto buckets don't have that
    property (boto bug)'''
    def __init__(self, name):
        s3_cxn = S3Connection()
        super(CloudFrontObject, self).__init__(s3_cxn.get_my_bucket(), name)

    def __repr__(self):
        return '<Object: %s>' % (self.name)

    def url(self, scheme='https'):
        url = '%s://' % scheme
        url += settings.AWS_CLOUDFRONT_DIST_HOSTNAME
        url += '/'
        url += self.name
        return url

    def generate_url(self, expires=None, begins=None, ipaddress=None):
        '''draconian URL generation, uses preset object expiry'''
        if expires is None:
            expires = int(time.time()) + settings.AWS_URL_LIFETIME
        policy = CloudFrontPolicy(self, expires, begins, ipaddress)
        return '%s?%s' % (self.url(), policy.query_string)

class CloudFrontStreamingObject(CloudFrontObject):
    '''A boto CloudFront "StreamingObject" replacement

    This doesn't use bucket.distribution, because boto buckets don't have that
    property (boto bug)'''
    def __repr__(self):
        return '<StreamingObject: %s>' % (self.name)

    def url(self, scheme='rtmpe'):
        '''Overrides scheme to rtmpe by default, adds mp4: prefix if needed'''

        url = '%s://' % scheme
        url += settings.AWS_CLOUDFRONT_STREAMING_DIST_HOSTNAME
        url += '/cfx/st/'
        url += self.name
        try:
            encoded_video = facade.models.EncodedVideo.objects.get(file=self.name)
            # Handle the mp4: prefix for h.264 vids
            if encoded_video.video_codec in ('libx264',):
                # Quick and easy, but possibly error-prone
                url = url.replace('cfx/st/', 'cfx/st/mp4:')
        except facade.models.EncodedVideo.DoesNotExist:
            logger.debug('Unabled to determine if video %s needs mp4 prefix; guessing based on extension' % self.name)
            base, extension = os.path.splitext(url)
            # All transcoded videos should be .f4v, so this is a safe guess
            if extension in ('.f4v',):
                url = url.replace('cfx/st/', 'cfx/st/mp4:')
        return url

    def generate_url(self, expires=None, begins=None, ipaddress=None):
        '''draconian URL generation, uses preset object expiry'''
        if expires is None:
            expires = int(time.time()) + settings.AWS_URL_LIFETIME
        policy = CloudFrontPolicy(self, expires, begins, ipaddress)
        return '%s?%s' % (self.url(), policy.query_string)

#=======================================================================
# S3 Helpers
#=======================================================================

# Iterating through the distributions sucks, but there's nothing in the Amazon
# API to make this easier. It would probably be faster/better to define the 
# CF distribution ID in the settings file.
class DistBucket(boto.s3.bucket.Bucket):
    '''An S3 Bucket with a CloudFront distribution attached'''
    def __init__(self, *args, **kwargs):
        super(DistBucket, self).__init__(*args, **kwargs)
        cf_cxn = CloudFrontConnection()
        distributions = cf_cxn.get_all_distributions()
        for distribution_summary in distributions:
            dist_bucket_name = distribution_summary.origin.split('.')[0]
            if dist_bucket_name == self.name:
                self.distribution = distribution_summary.get_distribution()
        try:
            getattr(self, 'distribution')
        except AttributeError:
            logger.error('No distribution for this bucket')

class StreamingDistBucket(boto.s3.bucket.Bucket):
    '''An S3 Bucket with a CloudFront distribution attached'''
    def __init__(self, *args, **kwargs):
        super(StreamingDistBucket, self).__init__(*args, **kwargs)
        cf_cxn = CloudFrontConnection()
        distributions = cf_cxn.get_all_streaming_distributions()
        for distribution_summary in distributions:
            dist_bucket_name = distribution_summary.origin.split('.')[0]
            if dist_bucket_name == self.name:
                self.distribution = distribution_summary.get_distribution()
        try:
            getattr(self, 'distribution')
        except AttributeError:
            logger.error('No streaming distribution for this bucket')

#===============================================================================
# ACL/Signed URL helpers
#===============================================================================

def b64awsencode(s):
    '''base64 encode for Amazon AWS, using -~_ instead of +/='''
    return base64.b64encode(s, altchars='-~').replace('=', '_')

def b64awsdecode(s):
    '''base64 decode for Amazon AWS, using -~_ instead of +/='''
    return base64.b64decode(s.replace('_', '='), altchars='-~')

class CloudFrontPolicy(object):
    def __init__(self, cf_object, expires, begins=None, ipaddress=None):
        self.cf_object = cf_object
        self.expires = expires
        self.begins = begins
        self.ipaddress = ipaddress

    def _query_string(self):
        '''Generate a signed query string for an Amazon CloudFront Object

        :param cf_obj: A cloudfront Object or StreamingObject
        :type cf_obj: boto.cloudfront.object.Object
        :param json_policy: JSON Policy to be signed in the query string
        :type json_policy: str
        This is just the query string part of making signed URLs
        '''
        json_policy = self.json_policy
        b64_json_policy = b64awsencode(json_policy)

        key = EVP.load_key_string(settings.AWS_CLOUDFRONT_SIGNING_KEY)
        # Explicitly use sha1 for signing, per AWS requirements
        key.reset_context(md='sha1')
        key.sign_init()
        key.sign_update(json_policy)
        signature = key.sign_final()

        b64_signature = b64awsencode(signature)

        query_string = "Policy=%s&Signature=%s&Key-Pair-Id=%s" % (
            b64_json_policy, b64_signature, settings.AWS_COULDFRONT_SIGNING_KEY_ID
        )

        return query_string

    def _json_policy(self):
        '''Create a JSON policy for signing'''
        resource = self.cf_object.url()

        # Handle cloudfront stream resource string
        if resource.lower().startswith('rtmp'):
            # Capture everything after /cfx/st/; just need the stream itself
            resource = resource.partition('/cfx/st/')[2]
            # The mp4: prefix should be excluded from the policy resource entry
            resource = resource.lstrip('mp4:')

        conditions = dict()
        conditions["DateLessThan"] = {"AWS:EpochTime": self.expires}

        if self.begins:
            conditions["DateGreaterThan"] = {"AWS:EpochTime": self.begins}

        if self.ipaddress:
            conditions["IpAddress"] = {"AWS:SourceIp": self.ipaddress}

        policy = {
            "Statement": [
                {
                    "Resource": resource,
                    "Condition": conditions,
                }
            ]
        }

        # separators remove whitespace, the strip is probably paranoid
        json_policy = json.dumps(policy, separators=(',',':'))
        logger.log(logging.getLevelName('TRACE'),
            'json custom policy: %s' % json_policy)

        return json_policy

    # Handy properties
    query_string = property(_query_string)
    json_policy = property(_json_policy)
