#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOD Servce Test Suite
#
# A test suite for the VOD service. To use it, you need to have a fully
# configured back-end running, pointed to by tests_svc_settings.py
# Copyright 2010 The American Research Institute, Inc.

from __future__ import with_statement

# Configure Django settings.
import django.core.management
settings_module = __import__('settings')
django.core.management.setup_environ(settings_module)
from django.conf import settings

import tests_svc_settings

import base64
import httplib
import os
import random
import time
import unittest
import urllib

def post_formdata(path, fields={}, files={}):
    rand = ''.join([chr(random.getrandbits(8)) for i in xrange(0,24)])
    BOUNDARY = '----my-boundary-' + base64.b64encode(rand)
    lines = []
    for name, value in fields.iteritems():
        lines.extend((
            '--' + BOUNDARY,
            'Content-Disposition: form-data; name="%s"' % name,
            '',
            str(value)))
    for fieldname, filename in files.iteritems():
        with open(filename, 'rb') as fh:
            lines.extend((
                '--' + BOUNDARY,
                'Content-Disposition: form-data; name="%s"; filename="%s"' %
                    (fieldname, os.path.basename(filename)),
                'Content-Type: application/octet-stream',
                '',
                fh.read()))
    lines.extend(('--' + BOUNDARY + '--', ''))
    body = '\r\n'.join(lines)
    h = httplib.HTTP(tests_svc_settings.SVC_TEST_HOST, tests_svc_settings.SVC_TEST_PORT)
    h.putrequest('POST', path)
    h.putheader('content-type', 'multipart/form-data; boundary=%s' % BOUNDARY)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode = h.getreply()[0]
    h.close()
    return errcode == 200

def upload_video(auth_token, video_file, name, description='a', author='a'):
    fields = {
        'auth_token' : auth_token,
        'name' : name,
        'description' : description,
        'author' : author,
        'categories' : '[{"id":1}]'
    }
    files = {'video' : video_file}
    path = '/%svod_aws/upload_video' % tests_svc_settings.SVC_TEST_PATH
    return post_formdata(path, fields, files)

def upload_video_photo(auth_token, video_id, photo_file, use_base64=False):
    fields = {
        'auth_token' : auth_token,
        'video_id' : video_id,
    }
    files = {}
    if use_base64:
        with open(photo_file, 'rb') as fh:
            fields['photo'] = base64.b64encode(fh.read())
    else:
        files['photo'] = photo_file
    path = '/%svod_aws/upload_video_photo' % tests_svc_settings.SVC_TEST_PATH
    return post_formdata(path, fields, files)

class svcGateway:
    # Generic 'svcGateway' class to support multiple service invocation methods
    # Currently supports 'amf' and 'xmlrpc'
    def __init__(self, service, url):
        if service == 'amf':
            self.service = service
            from pyamf.remoting.client import RemotingService
            self.svcGateway = RemotingService(url)
        elif service == 'xmlrpc':
            self.service = service
            from xmlrpclib import ServerProxy
            self.svcGateway = ServerProxy(url, allow_none=True)
        else:
            raise Exception, 'Valid services are "amf" and "xmlrpc"'

    def getService(self, service_name):
        if self.service == 'amf':
            return self.svcGateway.getService(service_name)
        if self.service == 'xmlrpc':
            return getattr(self.svcGateway, service_name)


class TestCase(unittest.TestCase):
    def setUp(self):
        self.svcGateway = svcGateway(service=tests_svc_settings.SVC_TEST, url=tests_svc_settings.SVC_TEST_URL)

        self.assignment_manager = self.svcGateway.getService('AssignmentManager')
        self.category_manager = self.svcGateway.getService('CategoryManager')
        self.encoded_video_manager = self.svcGateway.getService('EncodedVideoManager')
        self.group_manager = self.svcGateway.getService('GroupManager')
        self.user_manager = self.svcGateway.getService('UserManager')
        self.video_manager = self.svcGateway.getService('VideoManager')
        self.video_category_manager = self.svcGateway.getService('VideoCategoryManager')
        self.video_session_manager = self.svcGateway.getService('VideoSessionManager')

        self.admin_token = self.user_manager.login('admin', 'admin')['value']['auth_token']

        category_managers = self.group_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'Category Managers'}})['value'][0]['id']
        self.user_manager.create(self.admin_token, 'catman',
            'catmanspass', 'Mr.', 'Category', 'Manager', '555-1212',
            'cat@example.com', 'active', {'groups' : [category_managers]})
        self.catman_at = self.user_manager.login('catman', 'catmanspass')['value']['auth_token']
        cat_id = self.user_manager.get_authenticated_user(self.catman_at)['value']['id']
        self.category_manager.update(self.admin_token, 1,
            {'managers' : [cat_id]})
        self.group_manager.create(self.admin_token, 'viewers')
        viewers = self.group_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'viewers'}})['value'][0]['id']
        self.category_manager.update(self.admin_token, 1,
            {'authorized_groups' : [viewers]})
        self.user_manager.create(self.admin_token, 'view', 'viewspass', 'Mr.',
            'Video', 'Viewer', '555-1212', 'view@example.net', 'active',
            {'groups' : [viewers]})
        self.viewer_at = self.user_manager.login('view', 'viewspass')['value']['auth_token']
        self.user_manager.create(self.admin_token, 'upload', 'uploadspass',
            'Mr.', 'Video', 'Uploader', '555-1212', 'view@example.net',
            'active', {'organizations' : [1]})
        self.uploader_at = self.user_manager.login('upload', 'uploadspass')['value']['auth_token']

    def test_vod_upload_workflow(self):
        self.assertTrue(settings.VOD_ENABLE_VIDEO_UPLOAD_WORKFLOW)
        video_name = base64.b64encode(''.join([chr(random.getrandbits(8)) for i in xrange(0,6)]))
        self.assertTrue(upload_video(self.uploader_at,
            'vod_aws/test_data/720x480_4.3.mov', video_name))
        video_id = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : video_name}})['value'][0]['id']
        self.assertTrue(video_id > 0)
        # see that we get the default thumbnail
        photo_url = self.video_manager.get_filtered(self.catman_at,
            {'exact' : {'id' : video_id}}, ['photo_url'])['value'][0]['photo_url']
        self.assertTrue(photo_url.find('amazonaws') == -1, "Didn't get default URL")
        # wait for transcoding
        for tries in range(60):
            is_ready = self.video_manager.get_filtered(self.admin_token,
                {'exact' : {'id' : video_id}}, ['is_ready'])['value'][0]['is_ready']
            if is_ready: break
            time.sleep(5)
        else:
            self.fail('Timed out waiting for encoding to complete')
        # see that we now get the actual thumbnail
        photo_url = self.video_manager.get_filtered(self.catman_at,
            {'exact' : {'id' : video_id}}, ['photo_url'])['value'][0]['photo_url']
        self.assertTrue(photo_url.find('amazonaws') != -1, 'Got default URL')
        fh = urllib.urlopen(photo_url)
        self.assertTrue(fh.read(5) != '<?xml', 'Got an s3 error for %s' % photo_url)
        fh.close()
        # approve the video
        vc_id = self.video_category_manager.get_filtered(self.catman_at,
            {'exact' : {'video' : video_id, 'category' : 1}})['value'][0]['id']
        self.assertEquals(
            self.video_category_manager.update(self.catman_at, vc_id,
                {'status' : 'approved'})['status'],
            'OK')
        # create an assignment and see that we get the URLs
        assignment_id = self.assignment_manager.create(self.viewer_at,
            video_id)['value']['id']
        session = self.video_session_manager.create(self.viewer_at, assignment_id)
        for url in session['value']['urls']:
            print
            print url
        # let's change the thumbnail using the base64 png method
        self.assertTrue(upload_video_photo(self.catman_at, video_id,
            'vod_aws/test_data/randy_oj.png', True))
        # let's wait for the new thumbnail to upload and fetch its URL
        for tries in range(60):
            photo_url = self.video_manager.get_filtered(self.catman_at,
                {'exact' : {'id' : video_id}}, ['photo_url'])['value'][0]['photo_url']
            if photo_url.find('amazonaws') != -1 and photo_url.find('.png') != -1:
                break
            time.sleep(1)
        else:
            self.fail('Timed out waiting for thumbnail upload')
        fh = urllib.urlopen(photo_url)
        self.assertTrue(fh.read(5) != '<?xml', 'Got an s3 error for %s' % photo_url)
        fh.close()
        # let's change the thumbnail using the normal method
        self.assertTrue(upload_video_photo(self.catman_at, video_id,
            'vod_aws/test_data/biglebowski.jpg'))
        # let's wait for the new thumbnail to upload and fetch its URL
        for tries in range(60):
            photo_url = self.video_manager.get_filtered(self.catman_at,
                {'exact' : {'id' : video_id}}, ['photo_url'])['value'][0]['photo_url']
            if photo_url.find('amazonaws') != -1 and photo_url.find('.jpg') != -1:
                break
            time.sleep(1)
        else:
            self.fail('Timed out waiting for thumbnail upload')
        fh = urllib.urlopen(photo_url)
        self.assertTrue(fh.read(5) != '<?xml', 'Got an s3 error for %s' % photo_url)
        fh.close()
        # now let's reject the video and delete it
        self.assertEquals(
            self.video_category_manager.update(self.catman_at, vc_id,
                {'status' : 'rejected'})['status'],
            'OK')
        self.assertEquals(
            self.video_manager.delete(self.admin_token, video_id)['status'],
            'OK')


if __name__=='__main__':
    unittest.main()

# vim:tabstop=4 shiftwidth=4 expandtab
