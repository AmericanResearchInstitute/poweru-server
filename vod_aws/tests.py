# -*- coding: utf-8 -*-
"""Unit Tests for the vod_aws plugin

@copyright Copyright 2010 American Research Institute, Inc.

"""
from __future__ import with_statement

from datetime import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
import facade
import os
from pr_services.tests import TestCase, TestACLCRUD
from pr_services import exceptions, pr_time
import time

class VideoTestCase(TestCase):
    def setUp(self):
        self.initial_setup_args = ['precor']
        super(VideoTestCase, self).setUp()
        self.video_manager = facade.managers.VideoManager()
        self.video_category_manager = facade.managers.VideoCategoryManager()
        self.video_session_manager = facade.managers.VideoSessionManager()
        self.encoded_video_manager = facade.managers.EncodedVideoManager()
        self.category_manager = facade.managers.CategoryManager()

    def create_category_manager(self, title='Private', first_name='Category', last_name='Manager', label='1234 Test Address Lane', locality='Testville',
            region='NC', postal_code='12345', country='US', phone='378-478-3845'):
        username = self.user_manager.generate_username('', first_name, last_name)
        email = username+'@test.poweru.net'
        shipping_address = {'label' : label, 'locality' : locality, 'postal_code' : postal_code, 'country' : country, 'region' : region}
        billing_address = shipping_address
        category_manager_group_id = self.group_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Category Managers'}})[0]['id']
        category_manager = self.user_manager.create(self.admin_token, username, 'password', title, first_name, last_name, phone, email, 'active',
            {'name_suffix' : 'Jr.', 'shipping_address' : shipping_address, 'billing_address' : billing_address, 'groups' : [category_manager_group_id]})
        category_manager_at = facade.models.AuthToken.objects.get(session_id__exact=self.user_manager.login(username, 'password')['auth_token'])
        return category_manager, category_manager_at

    def _upload_video(self, auth_token, video_file_name, name='I Feel Great!',
            description='No really, I feel great!', categories=None,
            expected_return_code=200):
        """A helper method to upload a video from the test_data folder.

        The uploaded video will be the one named in video_file_name.  We return
        the Video object, and check the return value to make sure it equals
        expected_return_code.
        """
        video_file_name = os.path.join(os.path.dirname(__file__), 'test_data/%s'%video_file_name)
        with open(video_file_name, 'r') as video_file:
            postdata = {
                'auth_token' : auth_token.session_id,
                'name' : name,
                'description' : description,
                'author' : 'Unknown',
                'video' : video_file,
                'tags' : 'humor strategy licensure heavy',
            }
            if categories:
                postdata['categories'] = categories
            else:
                postdata['categories'] = '[{"id":1}]'
            response = self.client.post(reverse('vod_aws:upload_video'), postdata)
        self.assertEquals(response.status_code, expected_return_code)
        if expected_return_code != 200:
            return
        else:
            the_video_id = int(response.content)
            return facade.models.Video.objects.get(id=the_video_id)

    def _upload_video_photo(self, auth_token, video_id, thumbnail_file_name, expected_return_code=200):
        """A helper method to upload a video thumbnail from the test_data folder."""
        thumbnail_file_name = os.path.join(os.path.dirname(__file__), 'test_data/%s'%thumbnail_file_name)
        with open(thumbnail_file_name, 'r') as thumbnail_file:
            response = self.client.post(reverse('vod_aws:upload_video_photo'),
                {'auth_token' : auth_token.session_id, 'video_id' : video_id, 'photo' : thumbnail_file})
        self.assertEquals(response.status_code, expected_return_code)


class TestVideoTagging(VideoTestCase):
    def setUp(self):
        super(TestVideoTagging, self).setUp()

        self.video_1 = self.video_manager.create(self.admin_token, 'Video Number 1',
            '''This is a rather unnecessarily, ho-hum, yes, indeed, rather unnecessary
haha, unnecessary indeed! Rather unnecessary description for a video that doesn't
really exist, except in the imagination of a few good humans.

We aliens don't mind, however.  All of our videos are imaginary to humans.''',
            categories=[1])
        ret = self.video_manager.get_filtered(self.admin_token, {'member': {'id' : [self.video_1.id]}},
            ['tags'])
        self.assertEquals(len(ret), 1)
        self.assertEquals(ret[0]['tags'], [])

        self.video_2 = self.video_manager.create(self.admin_token, 'Video Number 2',
            '''Blah, blah, blah blah.  This is a description for video 2.''',
            categories=[1], optional_attributes={'tags': {'add': ['blah', 'uninteresting']}})
        ret = self.video_manager.get_filtered(self.admin_token, {'member': {'id' : [self.video_2.id]}},
            ['tags'])
        self.assertEquals(len(ret), 1)
        self.assertEquals(len(ret[0]['tags']), 2) 
        self.failUnless('blah' in ret[0]['tags'])
        self.failUnless('uninteresting' in ret[0]['tags'])
        
        self.video_3 = self.video_manager.create(self.admin_token, 'Video Number 3',
            '''Blah, blah, blah blah.  This is a description for video 3.''',
            categories=[1], optional_attributes={'tags': {'add': ['uninteresting']}})
        ret = self.video_manager.get_filtered(self.admin_token, {'member': {'id' : [self.video_3.id]}},
            ['tags'])
        self.assertEquals(len(ret), 1)
        self.assertEquals(len(ret[0]['tags']), 1) 
        self.failUnless('uninteresting' in ret[0]['tags'])
    
    def test_add_tags(self):
        self.video_manager.update(self.admin_token, self.video_1.id,
            {'tags' : {'add' : ['alien', 'unusual', 'imaginary']}})
        
        ret = self.video_manager.get_filtered(self.admin_token, {'member': {'id' : [self.video_1.id]}},
            ['tags'])
        self.assertEquals(len(ret), 1)
        self.failUnless(isinstance(ret[0]['tags'], list))
        self.assertEquals(len(ret[0]['tags']), 3)
        self.failUnless('alien' in ret[0]['tags'])
        self.failUnless('unusual' in ret[0]['tags'])
        self.failUnless('imaginary' in ret[0]['tags'])
        
        self.video_manager.update(self.admin_token, self.video_1.id,
            {'tags' : {'add' : ['extraterrestrial', 'facetious']}})
        
        ret = self.video_manager.get_filtered(self.admin_token, {'member': {'id' : [self.video_1.id]}},
            ['tags'])
        self.assertEquals(len(ret), 1)
        self.failUnless(isinstance(ret[0]['tags'], list))
        self.assertEquals(len(ret[0]['tags']), 5)
        self.failUnless('alien' in ret[0]['tags'])
        self.failUnless('unusual' in ret[0]['tags'])
        self.failUnless('imaginary' in ret[0]['tags'])
        self.failUnless('extraterrestrial' in ret[0]['tags'])
        self.failUnless('facetious' in ret[0]['tags'])
    
    def test_remove(self):
        self.video_manager.update(self.admin_token, self.video_1.id,
            {'tags' : {'add': ['one', 'two', 'three']}})
        
        ret = self.video_manager.get_filtered(self.admin_token, {'member': {'id' : [self.video_1.id]}},
            ['tags'])
        self.assertEquals(len(ret), 1)
        self.failUnless(isinstance(ret[0]['tags'], list))
        self.assertEquals(len(ret[0]['tags']), 3)
        self.failUnless('one' in ret[0]['tags'])
        self.failUnless('two' in ret[0]['tags'])
        self.failUnless('three' in ret[0]['tags'])
        
        self.video_manager.update(self.admin_token, self.video_1.id,
            {'tags' : {'remove': ['two', 'three']}})
        
        ret = self.video_manager.get_filtered(self.admin_token, {'member': {'id' : [self.video_1.id]}},
            ['tags'])
        self.assertEquals(len(ret), 1)
        self.failUnless(isinstance(ret[0]['tags'], list))
        self.assertEquals(len(ret[0]['tags']), 1)
        self.failUnless('one' in ret[0]['tags'])
        
        self.video_manager.update(self.admin_token, self.video_1.id,
            {'tags' : {'remove': [u'one'], 'add' : [u'onesimus', u'origen']}})
        
        ret = self.video_manager.get_filtered(self.admin_token, {'member': {'id' : [self.video_1.id]}},
            ['tags'])
        self.assertEquals(len(ret), 1)
        self.failUnless(isinstance(ret[0]['tags'], list))
        self.assertEquals(len(ret[0]['tags']), 2)
        self.failUnless(u'onesimus' in ret[0]['tags'])
        self.failUnless(u'origen' in ret[0]['tags'])
    
    def test_force_tags_to_lowercase(self):
        self.assertEquals(settings.FORCE_LOWERCASE_TAGS, True,
            'the FORCE_LOWERCASE_TAGS settings should be set to true for this unit test')
        self.video_manager.update(self.admin_token, self.video_1.id,
            {'tags' : {'add': [u'laurel', u'HArDy', u'FoO', u'中文的东西', u'Anschluß']}})
        
        ret = self.video_manager.get_filtered(self.admin_token, {'member': {'id' : [self.video_1.id]}},
            ['tags'])
        self.assertEquals(len(ret), 1)
        self.failUnless(isinstance(ret[0]['tags'], list))
        self.assertEquals(len(ret[0]['tags']), 5)
        self.failUnless(u'laurel' in ret[0]['tags'])
        self.failUnless(u'hardy' in ret[0]['tags'])
        self.failUnless(u'foo' in ret[0]['tags'])
        self.failUnless(u'中文的东西' in ret[0]['tags'])
        self.failUnless(u'anschluß' in ret[0]['tags'])
        
    def test_get_filtered_with_tags(self):
        ret = self.video_manager.get_filtered(self.admin_token,
            {'tag_union' : ['uninteresting']},
            ['name', 'tags'])
        self.assertEquals(len(ret), 2)
        pks = list()
        for video in ret:
            pks.append(video['id'])
        self.failUnless(self.video_2.id in pks)
        self.failUnless(self.video_3.id in pks)
        
        ret = self.video_manager.get_filtered(self.admin_token,
            {'tag_union' : ['blah', 'uninteresting']},
            ['name', 'tags'])
        self.assertEquals(len(ret), 2)
        pks = list()
        for video in ret:
            pks.append(video['id'])
        self.failUnless(self.video_2.id in pks)
        self.failUnless(self.video_3.id in pks)
        
        ret = self.video_manager.get_filtered(self.admin_token,
            {'tag_intersection' : ['blah', 'uninteresting']},
            ['name', 'tags'])
        self.assertEquals(len(ret), 1)
        self.assertEquals(ret[0]['id'], self.video_2.id)
        
        ret = self.video_manager.get_filtered(self.admin_token,
            {'or' : [{'tag_intersection' : ['blah', 'uninteresting']},
             {'icontains' : {'name': 'VIDEO number 1'}}]},
            ['name', 'tags'])
        self.assertEquals(len(ret), 2)
        pks = list()
        for video in ret:
            pks.append(video['id'])
        self.failUnless(self.video_1.id in pks)
        self.failUnless(self.video_2.id in pks)


class TestViews(VideoTestCase):
    def setUp(self):
        super(TestViews, self).setUp()
        user_role = self.org_role_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'User'}})[0]['id']
        cm_role = self.org_role_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'ContentManager'}})[0]['id']
        self.group = self.group_manager.create(self.admin_token, 'group1')
        self.watcher, self.watcher_at = self.create_student(group='group1')
        self.user_manager.update(self.admin_token, self.watcher.id,
            {'roles' : {'add' : [{'id' : user_role, 'organization' : self.organization1}]}})
        self.manager, self.manager_at = self.create_category_manager()
        self.user_manager.update(self.admin_token, self.manager.id,
            {'roles' : {'add' : [{'id' : cm_role, 'organization' : self.organization1}]}})
        self.cat1 = self.category_manager.create(self.admin_token, 'cat1')
        self.category_manager.update(self.admin_token, self.cat1.id, {
            'authorized_groups' : [self.group.id],
            'managers' : [self.manager.id]})
        self.cat2 = self.category_manager.create(self.admin_token, 'cat2')
        self.category_manager.update(self.admin_token, self.cat2.id, {
            'authorized_groups' : [self.group.id],
            'managers' : [self.manager.id],
            'locked' : True})
        self.cat3 = self.category_manager.create(self.admin_token, 'cat3')
        self.video = self._upload_video(self.admin_token, '720x480_4.3.mov',
            name='video1', description='approved video',
            categories=('[{"id":%d},{"id":%d}]' % (self.cat1.id, self.cat3.id)))
        self.vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video.id, 'category' : self.cat1.id}})[0]['id']
        self.video_category_manager.update(self.admin_token, self.vc,
            {'status' : 'approved'})
        self.vc2 = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video.id, 'category' : self.cat3.id}})[0]['id']
        # Add some fake encoded videos
        self.ev1 = facade.models.EncodedVideo.objects.create(
            video=self.video, bitrate='128')
        self.ev2 = facade.models.EncodedVideo.objects.create(
            video=self.video, bitrate='256')

    def test_admin_categories_view(self):
        wanted_view = {
            'id' : self.cat2.id,
            'name' : 'cat2',
            'managers' : [{
                'id' : self.manager.id,
                'first_name' : self.manager.first_name,
                'last_name' : self.manager.last_name,
                'email' : self.manager.email,
            }],
            'authorized_groups' : [{
                'id' : self.group.id,
                'name' : 'group1',
            }],
            'locked' : True,
        }
        categories = self.category_manager.admin_categories_view(self.admin_token)
        category = filter(lambda x: x['id'] == self.cat2.id, categories)[0]
        self.assertEqual(category, wanted_view)
        categories = self.category_manager.admin_categories_view(self.manager_at)
        category = filter(lambda x: x['id'] == self.cat2.id, categories)[0]
        self.assertEqual(category, wanted_view)

    def test_user_videos_view(self):
        wanted_view = {
            'id' : self.video.id,
            'name' : 'video1',
            'description' : 'approved video',
            'author' : 'Unknown',
            'length' : '',
            'num_views' : 0,
            'approved_categories' : [{
                'id' : self.cat1.id,
                'name' : 'cat1',
            }],
            'encoded_videos' : [
                {'id' : self.ev1.id, 'bitrate': u'128', 'url' : None},
                {'id' : self.ev2.id, 'bitrate': u'256', 'url' : None},
            ],
            'photo_url' : settings.MEDIA_URL + settings.VOD_TEMP_THUMBNAIL,
            'src_file_size' : 5375808,
            'create_timestamp' : self.video.create_timestamp.replace(
                microsecond=0, tzinfo=pr_time.UTC()).isoformat(),
        }
        videos = self.video_manager.user_videos_view(self.watcher_at)
        video = filter(lambda x: x['id'] == self.video.id, videos)[0]
        self.assertEqual(video, wanted_view)

    def test_admin_videos_view(self):
        wanted_view = {
            'id' : self.video.id,
            'name' : 'video1',
            'description' : 'approved video',
            'author' : 'Unknown',
            'length' : '',
            'num_views' : 0,
            'category_relationships' : [
                {
                    'id' : self.vc,
                    'category' : self.cat1.id,
                    'category_name' : 'cat1',
                    'status' : 'approved',
                },
                {
                    'id' : self.vc2,
                    'category' : self.cat3.id,
                    'category_name' : 'cat3',
                    'status' : 'pending',
                },
            ],
            'encoded_videos' : [
                {'id' : self.ev1.id, 'bitrate': u'128', 'url' : None, 'http_url' : None},
                {'id' : self.ev2.id, 'bitrate': u'256', 'url' : None, 'http_url' : None},
            ],
            'photo_url' : settings.MEDIA_URL + settings.VOD_TEMP_THUMBNAIL,
            'src_file_size' : 5375808,
            'create_timestamp' : self.video.create_timestamp.replace(
                microsecond=0, tzinfo=pr_time.UTC()).isoformat(),
        }
        videos = self.video_manager.admin_videos_view(self.admin_token)
        video = filter(lambda x: x['id'] == self.video.id, videos)[0]
        self.assertEqual(video, wanted_view)
        # category managers can't see EncodedVideo.http_url
        for ev in wanted_view['encoded_videos']:
            del ev['http_url']
        videos = self.video_manager.admin_videos_view(self.manager_at)
        video = filter(lambda x: x['id'] == self.video.id, videos)[0]
        self.assertEqual(video, wanted_view)

    def test_admin_groups_view(self):
        wanted_view = {
            'id' : self.group.id,
            'name' : 'group1',
            'categories' : [
                {'id' : self.cat1.id, 'name' : 'cat1'},
                {'id' : self.cat2.id, 'name' : 'cat2'},
            ],
        }
        groups = self.group_manager.vod_admin_groups_view(self.admin_token)
        group = filter(lambda x: x['id'] == self.group.id, groups)[0]
        self.assertEqual(group, wanted_view)

    def test_watcher_report(self):
        # need a second video
        self.video2 = self.video_manager.create(self.admin_token, 'video2',
            'approved video 2', categories=[self.cat1.id])
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video2.id, 'category' : self.cat1.id}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'approved'})
        # need 6 watchers
        w1, at1 = self.create_student(group='group1')
        w2, at2 = self.create_student(group='group1')
        w3, at3 = self.create_student(group='group1')
        w4, at4 = self.create_student(group='group1')
        w5, at5 = self.create_student(group='group1')
        w6, at6 = self.create_student(group='group1')
        # they need to watch some videos
        s1 = self.video_session_manager.register_video_view(at1, self.video.id)['id']
        s2 = self.video_session_manager.register_video_view(at2, self.video2.id)['id']
        time.sleep(1)
        t1 = datetime.utcnow().replace(microsecond=0, tzinfo=pr_time.UTC()).isoformat()
        time.sleep(1)
        s3 = self.video_session_manager.register_video_view(at3, self.video.id)['id']
        s4 = self.video_session_manager.register_video_view(at4, self.video2.id)['id']
        time.sleep(1)
        t2 = datetime.utcnow().replace(microsecond=0, tzinfo=pr_time.UTC()).isoformat()
        time.sleep(1)
        s5 = self.video_session_manager.register_video_view(at5, self.video.id)['id']
        s6 = self.video_session_manager.register_video_view(at6, self.video2.id)['id']
        # helper
        def check_sessions(result):
            sess_data = {
                s1 : {'user' : w1.id, 'video' : self.video.id},
                s2 : {'user' : w2.id, 'video' : self.video2.id},
                s3 : {'user' : w3.id, 'video' : self.video.id},
                s4 : {'user' : w4.id, 'video' : self.video2.id},
                s5 : {'user' : w5.id, 'video' : self.video.id},
                s6 : {'user' : w6.id, 'video' : self.video2.id},
            }
            sessions = []
            for sess in result:
                sessions.append(sess['id'])
                self.assertTrue(sess.has_key('date_started'))
                self.assertTrue(sess.has_key('user'))
                self.assertEqual(sess['user']['id'],
                    sess_data[sess['id']]['user'])
                for key in ['default_username_and_domain', 'email', 'first_name', 'last_name']:
                    self.assertTrue(sess['user'].has_key(key))
                self.assertTrue(sess.has_key('video'))
                self.assertEqual(sess['video']['id'],
                    sess_data[sess['id']]['video'])
                self.assertTrue(sess['video'].has_key('name'))
            return set(sessions)
        # let's try to see all of them
        result = self.video_session_manager.watcher_report(self.manager_at,
            [self.video.id, self.video2.id])
        self.assertEqual(check_sessions(result), set((s1, s2, s3, s4, s5 , s6)))
        # now the first video, after t1
        result = self.video_session_manager.watcher_report(self.manager_at,
            [self.video.id], start_date=t1)
        self.assertEqual(check_sessions(result), set((s3, s5)))
        # now the second video, before t2
        result = self.video_session_manager.watcher_report(self.manager_at,
            [self.video2.id], end_date=t2)
        self.assertEqual(check_sessions(result), set((s2, s4)))
        # both videos again, between t1 and t2
        result = self.video_session_manager.watcher_report(self.manager_at,
            [self.video.id, self.video2.id], start_date=t1, end_date=t2)
        self.assertEqual(check_sessions(result), set((s3, s4)))

    def test_viewing_activity_report(self):
        # need 2 more videos
        self.video2 = self.video_manager.create(self.admin_token, 'video2',
            'approved video 2', categories=[self.cat1.id])
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video2.id, 'category' : self.cat1.id}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'approved'})
        self.video3 = self.video_manager.create(self.admin_token, 'video3',
            'approved video 3', categories=[self.cat1.id])
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video3.id, 'category' : self.cat1.id}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'approved'})
        # need 2 watchers
        w1, at1 = self.create_student(group='group1')
        w2, at2 = self.create_student(group='group1')
        # they need to watch some videos
        s1 = self.video_session_manager.register_video_view(at1, self.video.id)['id']
        s2 = self.video_session_manager.register_video_view(at2, self.video.id)['id']
        time.sleep(1)
        t1 = datetime.utcnow().replace(microsecond=0, tzinfo=pr_time.UTC()).isoformat()
        time.sleep(1)
        s3 = self.video_session_manager.register_video_view(at1, self.video2.id)['id']
        s4 = self.video_session_manager.register_video_view(at2, self.video2.id)['id']
        time.sleep(1)
        t2 = datetime.utcnow().replace(microsecond=0, tzinfo=pr_time.UTC()).isoformat()
        time.sleep(1)
        s5 = self.video_session_manager.register_video_view(at1, self.video3.id)['id']
        s6 = self.video_session_manager.register_video_view(at2, self.video3.id)['id']
        # helper
        def check_sessions(result):
            sess_data = {
                s1 : {'user' : w1.id, 'video' : self.video.id},
                s2 : {'user' : w2.id, 'video' : self.video.id},
                s3 : {'user' : w1.id, 'video' : self.video2.id},
                s4 : {'user' : w2.id, 'video' : self.video2.id},
                s5 : {'user' : w1.id, 'video' : self.video3.id},
                s6 : {'user' : w2.id, 'video' : self.video3.id},
            }
            sessions = []
            for sess in result:
                sessions.append(sess['id'])
                self.assertTrue(sess.has_key('date_started'))
                self.assertTrue(sess.has_key('user'))
                self.assertEqual(sess['user']['id'],
                    sess_data[sess['id']]['user'])
                for key in ['username', 'email', 'first_name', 'last_name']:
                    self.assertTrue(sess['user'].has_key(key))
                self.assertTrue(sess.has_key('video'))
                self.assertEqual(sess['video']['id'],
                    sess_data[sess['id']]['video'])
                for key in ['name', 'author', 'description']:
                    self.assertTrue(sess['video'].has_key(key))
            return set(sessions)
        # let's try to see all of them
        result = self.video_session_manager.viewing_activity_report(
            self.manager_at, [w1.id, w2.id])
        self.assertEqual(check_sessions(result), set((s1, s2, s3, s4, s5 , s6)))
        # now the first watcher, after t1
        result = self.video_session_manager.viewing_activity_report(
            self.manager_at, [w1.id], start_date=t1)
        self.assertEqual(check_sessions(result), set((s3, s5)))
        # now the second watcher, before t2
        result = self.video_session_manager.viewing_activity_report(
            self.manager_at, [w2.id], end_date=t2)
        self.assertEqual(check_sessions(result), set((s2, s4)))
        # both watchers again, between t1 and t2
        result = self.video_session_manager.viewing_activity_report(
            self.manager_at, [w1.id, w2.id], start_date=t1, end_date=t2)
        self.assertEqual(check_sessions(result), set((s3, s4)))


class TestVideoSystem(VideoTestCase):
    def test_upload_video(self):
        # we rely on the fixture to create at least 2 categories
        # test invalid JSON
        self._upload_video(self.admin_token, '720x480_4.3.mov',
            categories="[{'id':1},{'id':2}]", expected_return_code=400)
        # valid JSON, but top level isn't a list
        self._upload_video(self.admin_token, '720x480_4.3.mov',
            categories='{"id":1}', expected_return_code=400)
        # valid JSON, but second level isn't a dict
        self._upload_video(self.admin_token, '720x480_4.3.mov',
            categories='[[1]]', expected_return_code=400)
        # valid JSON, but second level dict doesn't contain integer id
        self._upload_video(self.admin_token, '720x480_4.3.mov',
            categories='[{"od":1}]', expected_return_code=400)
        self._upload_video(self.admin_token, '720x480_4.3.mov',
            categories='[{"id":"a"}]', expected_return_code=400)
        # category doesn't exist
        self._upload_video(self.admin_token, '720x480_4.3.mov',
            categories='[{"id":1000}]', expected_return_code=400)
        # test normal scenario
        time_before_create = datetime.utcnow().replace(microsecond=0)
        video = self._upload_video(self.admin_token, '720x480_4.3.mov',
            categories='[{"id":1},{"id":2}]')
        time_after_create = datetime.utcnow()
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : video.id}},
            ['name', 'description', 'author', 'create_timestamp',
                'categories','category_relationships'])[0]
        # check metadata
        self.assertEqual(result['name'], 'I Feel Great!')
        self.assertEqual(result['description'], 'No really, I feel great!')
        self.assertEqual(result['author'], 'Unknown')
        # check that category relationships are pending
        self.assertTrue(len(result['categories']) == 2)
        for crid in result['category_relationships']:
            cr = self.video_category_manager.get_filtered(self.admin_token,
                {'exact' : {'id' : crid}}, ['status'])[0]
            self.assertEquals(cr['status'], 'pending')
        # test create timestamp
        self.assertTrue('create_timestamp' in result)
        result = facade.models.Video.objects.get(id=result['id'])
        self.assertTrue(time_before_create <= result.create_timestamp)
        self.assertTrue(time_after_create >= result.create_timestamp)
        # test normal scenario with extra data in the JSON dicts
        video = self._upload_video(self.admin_token, '720x480_4.3.mov',
            categories='[{"id":1,"name":"foo"},{"id":2,"fish":"trout"}]')
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : video.id}},
            ['categories','category_relationships'])[0]
        self.assertTrue(len(result['categories']) == 2)

    def test_upload_video_form(self):
        response = self.client.get(reverse('vod_aws:upload_video_form', args=[self.admin_token.session_id]))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'vod_upload_video.html')
        video_file_name = os.path.join(os.path.dirname(__file__), 'test_data/%s' % '720x480_4.3.mov')
        time_before_create = datetime.utcnow().replace(microsecond=0)
        with open(video_file_name, 'r') as video_file:
            response = self.client.post(reverse('vod_aws:upload_video_form', args=[self.admin_token.session_id]),
                {'name' : 'test video form upload', 'description' : 'No really, I feel great!',
                'author' : 'Unknown', 'video' : video_file,
                'categories' : '[{"id":1}]'})
            self.assertEquals(response.status_code, 200)
        time_after_create = datetime.utcnow()
        the_video = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'test video form upload'}},
            ['name', 'description', 'author', 'tags', 'create_timestamp'])[0]
        self.assertEquals(the_video['name'], 'test video form upload')
        self.assertEquals(the_video['description'], 'No really, I feel great!')
        self.assertEquals(the_video['author'], 'Unknown')
        self.assertTrue('create_timestamp' in the_video)
        the_video = facade.models.Video.objects.get(id=the_video['id'])
        self.assertTrue(time_before_create <= the_video.create_timestamp)
        self.assertTrue(time_after_create >= the_video.create_timestamp)

    def _check_assignments_and_sessions(self):
        assignments = [ x['id'] for x in
            self.assignment_manager.get_filtered(self.admin_token, {})]
        self.assertEqual(set(self._expect_assignments), set(assignments))
        sessions = [ (s['id'], s['assignment']) for s in
            self.video_session_manager.get_filtered(self.admin_token,
            {}, ['assignment']) ]
        self.assertEquals(set(self._expect_sessions), set(sessions))
        
    def test_register_video_view(self):
        group = self.group_manager.create(self.admin_token, 'group1')
        self.category_manager.update(self.admin_token, 1,
            {'authorized_groups' : [group.id]})
        student, student_at = self.create_student(group='group1')
        video = self._upload_video(self.admin_token, '720x480_4.3.mov')
        self.video_category_manager.update(self.admin_token,
            video.category_relationships.all()[0].id, {'status' : 'approved'})
        self._expect_assignments = []
        self._expect_sessions = []
        # no assignment, no session
        session = self.video_session_manager.register_video_view(
            student_at, video.id)['id']
        assignment = self.assignment_manager.get_filtered(self.admin_token,
            {'exact' : {'user' : student.id}})[0]['id']
        self._expect_assignments.append(assignment)
        self._expect_sessions.append((session, assignment))
        self._check_assignments_and_sessions()
        # delete the session we just created
        self.video_session_manager.delete(self.admin_token, session)
        self._expect_sessions.remove((session, assignment))
        # assignment, no session
        session = self.video_session_manager.register_video_view(
            student_at, video.id)['id']
        self._expect_sessions.append((session, assignment))
        self._check_assignments_and_sessions()
        # assignment, fresh session
        same_session = self.video_session_manager.register_video_view(
            student_at, video.id)['id']
        self.assertEqual(same_session, session)
        self._check_assignments_and_sessions()
        # now make the session appear to be old
        the_past = self.right_now - self.one_day
        self.video_session_manager.update(self.admin_token, session,
            {'date_started' : the_past.isoformat()})
        # assignment, old session
        session = self.video_session_manager.register_video_view(
            student_at, video.id)['id']
        self._expect_sessions.append((session, assignment))
        self._check_assignments_and_sessions()
        # now make a second assignment of the same video
        assignment = self.assignment_manager.create(student_at, video.id).id
        self._expect_assignments.append(assignment)
        # two assignments, no session on new one
        session = self.video_session_manager.register_video_view(
            student_at, video.id)['id']
        self._expect_sessions.append((session, assignment))
        self._check_assignments_and_sessions()
        # two assignments, fresh session on new one
        same_session = self.video_session_manager.register_video_view(
            student_at, video.id)['id']
        self.assertEqual(same_session, session)
        self._check_assignments_and_sessions()
        # now make the session appear to be old
        self.video_session_manager.update(self.admin_token, session,
            {'date_started' : the_past.isoformat()})
        # two assignments, 'old' session on new one
        session = self.video_session_manager.register_video_view(
            student_at, video.id)['id']
        self._expect_sessions.append((session, assignment))
        self._check_assignments_and_sessions()
        # second video for same user
        video2 = self._upload_video(self.admin_token, '720x480_4.3.mov')
        self.video_category_manager.update(self.admin_token,
            video2.category_relationships.all()[0].id, {'status' : 'approved'})
        session = self.video_session_manager.register_video_view(
            student_at, video2.id)['id']
        assignment = self.assignment_manager.get_filtered(self.admin_token,
            {'exact' : {'user' : student.id, 'task' : video2.id}})[0]['id']
        self._expect_assignments.append(assignment)
        self._expect_sessions.append((session, assignment))
        self._check_assignments_and_sessions()
        # second user for original video
        student2, student2_at = self.create_student(group='group1')
        session = self.video_session_manager.register_video_view(
            student2_at, video.id)['id']
        assignment = self.assignment_manager.get_filtered(self.admin_token,
            {'exact' : {'user' : student2.id, 'task' : video.id}})[0]['id']
        self._expect_assignments.append(assignment)
        self._expect_sessions.append((session, assignment))
        self._check_assignments_and_sessions()
        # let's check the users_who_watched and num_views video properties
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : video.id}}, ['users_who_watched', 'num_views'])[0]
        self.assertEqual(len(result['users_who_watched']), 2)
        self.assertTrue(student.id in result['users_who_watched'])
        self.assertTrue(student2.id in result['users_who_watched'])
        self.assertEqual(result['num_views'], 5)
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : video2.id}}, ['users_who_watched', 'num_views'])[0]
        self.assertEqual(len(result['users_who_watched']), 1)
        self.assertTrue(student.id in result['users_who_watched'])
        self.assertEqual(result['num_views'], 1)
        # finally, let's test get_num_views_by_date
        result = self.video_manager.get_num_views_by_date(self.admin_token,
            {'exact' : {'id' : video.id}}, ['name'],
            (self.right_now-self.one_day*3).isoformat(),
            (self.right_now-self.one_day*2).isoformat())[0]
        self.assertEqual(result['num_views'], 0)
        result = self.video_manager.get_num_views_by_date(self.admin_token,
            {'exact' : {'id' : video.id}}, ['name'],
            (self.right_now-self.one_day*2).isoformat(),
            (self.right_now-self.one_day).isoformat())[0]
        self.assertEqual(result['num_views'], 2) # we fake 2 day-old sessions
        result = self.video_manager.get_num_views_by_date(self.admin_token,
            {'exact' : {'id' : video.id}}, ['name'],
            self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat())[0]
        self.assertEqual(result['num_views'], 3) # the rest should be current
        result = self.video_manager.get_num_views_by_date(self.admin_token,
            {'exact' : {'id' : video.id}}, ['name'],
            (self.right_now+self.one_day).isoformat(),
            (self.right_now+self.one_day*2).isoformat())[0]
        self.assertEqual(result['num_views'], 0)

    def test_locking_categories(self):
        cat = self.category_manager.create(self.admin_token, 'acat')
        cat2 = self.category_manager.create(self.admin_token, 'anothercat')
        video = self._upload_video(self.admin_token, '720x480_4.3.mov',
            categories=('[{"id":%d}]' % cat.id))
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : video.id}}, ['categories'])[0]
        self.assertEquals(result['categories'], [cat.id])
        self.category_manager.update(self.admin_token, cat.id, {'locked' : True})
        self.video_manager.update(self.admin_token, video.id,
            {'categories' : {'add' : [cat2.id]}})
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : video.id}}, ['categories'])[0]
        self.assertEqual(len(result['categories']), 2)
        self.assertTrue(cat.id in result['categories'])
        self.assertTrue(cat2.id in result['categories'])
        self.video_manager.update(self.admin_token, video.id,
            {'categories' : {'remove' : [cat2.id]}})
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : video.id}}, ['categories'])[0]
        self.assertEquals(result['categories'], [cat.id])
        self.video_manager.update(self.admin_token, video.id,
            {'categories' : {'remove' : [cat.id]}})
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : video.id}}, ['categories'])[0]
        self.assertEquals(result['categories'], [])
        self.assertRaises(facade.models.ModelDataValidationError,
            self.video_manager.update, self.admin_token, video.id,
            {'categories' : {'add' : [cat.id]}})
        self.category_manager.update(self.admin_token, cat.id, {'locked' : False})
        self.video_manager.update(self.admin_token, video.id,
            {'categories' : {'add' : [cat.id]}})
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : video.id}}, ['categories'])[0]
        self.assertEquals(result['categories'], [cat.id])

    def test_delete_video(self):
        # test that we can't delete a video until it's been rejected in every
        # category
        video = self.video_manager.create(self.admin_token, 'a video',
            'a video', categories=[1,2])
        self.assertRaises(exceptions.OperationNotPermittedException,
            self.video_manager.delete, self.admin_token, video.id)
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : video.id, 'category' : 1}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'rejected'})
        self.assertRaises(exceptions.OperationNotPermittedException,
            self.video_manager.delete, self.admin_token, video.id)
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : video.id, 'category' : 2}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'rejected'})
        self.video_manager.delete(self.admin_token, video.id)

    def test_default_group(self):
        default_groups = [g['id'] for g in self.group_manager.get_filtered(
            self.admin_token, {'exact' : {'default' : True}})]
        catman_group = self.group_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'Category Managers'}})[0]['id']
        # admin creates a user with no explicit groups
        student, student_at = self.create_student(group=None)
        result = self.user_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : student.id}}, ['groups'])[0]
        self.assertEqual(set(result['groups']), set(default_groups))
        # admin creates a user with an explicit group
        catman, catman_at = self.create_category_manager()
        result = self.user_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : catman.id}}, ['groups'])[0]
        self.assertEqual(set(result['groups']),
            set(default_groups+[catman_group]))
        # user self-registers
        username = self.user_manager.generate_username('', 'Elvis', 'Presley')
        email = username+'@electronsweatshop.com'
        elvis = self.user_manager.create(self.admin_token, username, 'password',
            'King', 'Elvis', 'Presley', '777-687-5309', email, 'active')
        result = self.user_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : elvis.id}}, ['groups'])[0]
        self.assertEqual(set(result['groups']), set(default_groups))


class TestVideoAuthz(VideoTestCase):
    def setUp(self):
        super(TestVideoAuthz, self).setUp()
        user_role = self.org_role_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'User'}})[0]['id']
        cm_role = self.org_role_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'ContentManager'}})[0]['id']
        self.cat1 = self.category_manager.create(self.admin_token, 'cat1')
        self.cat1_group = self.group_manager.create(self.admin_token, 'group1')
        self.cat1_watcher, self.cat1_watcher_at = self.create_student(group='group1')
        self.user_manager.update(self.admin_token, self.cat1_watcher.id,
            {'roles' : {'add' : [{'id' : user_role, 'organization' : self.organization1}]}})
        self.cat1_man, self.cat1_man_at = self.create_category_manager()
        self.user_manager.update(self.admin_token, self.cat1_man.id,
            {'roles' : {'add' : [{'id' : cm_role, 'organization' : self.organization1}]}})
        self.category_manager.update(self.admin_token, self.cat1.id, {
            'authorized_groups' : [self.cat1_group.id],
            'managers' : [self.cat1_man.id]})
        self.cat2 = self.category_manager.create(self.admin_token, 'cat2')
        self.cat2_group = self.group_manager.create(self.admin_token, 'group2')
        self.cat2_watcher, self.cat2_watcher_at = self.create_student(group='group2')
        self.user_manager.update(self.admin_token, self.cat2_watcher.id,
            {'roles' : {'add' : [{'id' : user_role, 'organization' : self.organization1}]}})
        self.cat2_man, self.cat2_man_at = self.create_category_manager()
        self.user_manager.update(self.admin_token, self.cat2_man.id,
            {'roles' : {'add' : [{'id' : cm_role, 'organization' : self.organization1}]}})
        self.category_manager.update(self.admin_token, self.cat2.id, {
            'authorized_groups' : [self.cat2_group.id],
            'managers' : [self.cat2_man.id]})
        self.cat3 = self.category_manager.create(self.admin_token, 'cat3')
        self.category_manager.update(self.admin_token, self.cat3.id, {
            'managers' : [self.cat1_man.id]})
        self.cat4 = self.category_manager.create(self.admin_token, 'cat4')
        self.category_manager.update(self.admin_token, self.cat4.id, {
            'managers' : [self.cat1_man.id]})
        self.uploader, self.uploader_at = self.create_student(group=None)
        self.user_manager.update(self.admin_token, self.uploader.id,
            {'roles' : {'add' : [{'id' : user_role, 'organization' : self.organization1}]}})
        self.luser, self.luser_at = self.create_student(group=None)
        
        self.video1 = self.video_manager.create(self.admin_token, 'video1',
            'approved video', categories=[self.cat1.id, self.cat2.id])
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video1.id, 'category' : self.cat1.id}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'approved'})
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video1.id, 'category' : self.cat2.id}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'rejected'})
        self.encoded_video_manager.create(self.admin_token, '128', self.video1.id)
        self.video2 = self.video_manager.create(self.admin_token, 'video2',
            'pending video', categories=[self.cat1.id, self.cat2.id])
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video2.id, 'category' : self.cat2.id}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'rejected'})
        self.encoded_video_manager.create(self.admin_token, '128', self.video2.id)
        self.video3 = self.video_manager.create(self.admin_token, 'video3',
            'rejected video', categories=[self.cat1.id])
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video3.id, 'category' : self.cat1.id}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'rejected'})
        self.encoded_video_manager.create(self.admin_token, '128', self.video3.id)
        self.video4 = self.video_manager.create(self.admin_token, 'video4',
            'deleted video', categories=[self.cat1.id])
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video4.id, 'category' : self.cat1.id}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'rejected'})
        self.encoded_video_manager.create(self.admin_token, '128', self.video4.id)
        self.video_manager.delete(self.admin_token, self.video4.id)

    def test_category_model(self):
        # test approved_videos
        result = self.category_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : self.cat1.id}}, ['approved_videos'])[0]
        self.assertEquals(result['approved_videos'], [self.video1.id])
        result = self.category_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : self.cat2.id}}, ['approved_videos'])[0]
        self.assertEquals(result['approved_videos'], [])
        # test reading
        want = {
          'luser_at' : None,
          'uploader_at' : ['id', 'name', 'locked'],
          'cat1_watcher_at' : ['id', 'name', 'locked', 'approved_videos'],
          'cat2_watcher_at' : ['id', 'name', 'locked'],
          'cat1_man_at' : ['id', 'managers', 'name', 'locked',
                           'approved_videos', 'videos', 'authorized_groups'],
          'cat2_man_at' : ['id', 'name', 'locked'],
        }
        for actor_at, want_fields in want.iteritems():
            result = self.category_manager.get_filtered(getattr(self, actor_at),
                {'exact' : {'id' : self.cat1.id}},
                ['authorized_groups', 'managers', 'name', 'locked', 'videos',
                    'approved_videos'])
            if want_fields:
                self.assertEqual(set(result[0].keys()), set(want_fields))
            else:
                self.assertEqual(len(result), 0)
        # test updating authorized_groups
        newgroup = self.group_manager.create(self.admin_token, 'newgroup')
        for actor_at in ['luser_at', 'uploader_at', 'cat1_watcher_at',
                         'cat2_watcher_at', 'cat2_man_at']:
            self.assertRaises(exceptions.PermissionDeniedException,
                self.category_manager.update, getattr(self, actor_at),
                self.cat1.id, {'authorized_groups' : {'add' : [newgroup.id]}})
        self.category_manager.update(self.cat1_man_at, self.cat1.id,
            {'authorized_groups' : {'add' : [newgroup.id]}})
        result = self.category_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : self.cat1.id}}, ['authorized_groups'])[0]
        self.assertEqual(set(result['authorized_groups']),
            set((self.cat1_group.id, newgroup.id)))

    def test_group_model(self):
        # test who can see what groups
        all_groups = [g['name'] for g in
            self.group_manager.get_filtered(self.admin_token, {}, ['name'])]
        want = {
          'cat1_man_at' : all_groups,
          'cat2_man_at' : all_groups,
          'cat1_watcher_at' : ['Default', 'group1'],
          'cat2_watcher_at' : ['Default', 'group2'],
          'uploader_at' : ['Default'],
          'luser_at' : ['Default'],
        }
        for actor_at, want_groups in want.iteritems():
            result = self.group_manager.get_filtered(getattr(self, actor_at),
                {}, ['name', 'users', 'managers'])
            fields = set()
            for r in result: fields.update(r.keys())
            groups = set(g['name'] for g in result)
            self.assertEqual(groups, set(want_groups))
            if len(groups):
                self.assertEqual(fields, set(('id', 'name')))
            else:
                self.assertEqual(fields, set())

    def test_video_category_model(self):
        # test reading
        for actor_at in ['luser_at', 'uploader_at', 'cat1_watcher_at',
                         'cat2_watcher_at']:
            result = self.video_category_manager.get_filtered(
                getattr(self, actor_at), {},
                ['status', 'category', 'category_name', 'video'])
            self.assertEqual(len(result), 0)
        for actor_at in ['cat1_man_at', 'cat2_man_at']:
            result = self.video_category_manager.get_filtered(
                getattr(self, actor_at), {},
                ['status', 'category', 'category_name', 'video'])
            self.assertEqual(len(result), 5)
            self.assertEqual(set(r['video'] for r in result),
                set((self.video1.id, self.video2.id, self.video3.id)))
            for r in result:
                self.assertEqual(set(r.keys()), set((
                    ['id', 'status', 'category', 'category_name', 'video'])))
        # test updating status (non-deleted)
        vcr_id = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'category' : self.cat1.id, 'video' : self.video2.id}})[0]['id']
        for actor_at in ['luser_at', 'uploader_at', 'cat1_watcher_at',
                         'cat2_watcher_at', 'cat2_man_at']:
            self.assertRaises(exceptions.PermissionDeniedException,
                self.video_category_manager.update, getattr(self, actor_at),
                vcr_id, {'status' : 'approved'})
        self.video_category_manager.update(self.cat1_man_at, vcr_id,
            {'status' : 'approved'})
        result = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'category' : self.cat1.id, 'video' : self.video2.id}},
            ['status'])[0]
        self.assertEqual(result['status'], 'approved')
        # test that even the video's category manager can't update deleted videos
        vcr_id = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'category' : self.cat1.id, 'video' : self.video4.id}})[0]['id']
        self.assertRaises(exceptions.PermissionDeniedException,
            self.video_category_manager.update, self.cat1_man_at,
            vcr_id, {'status' : 'approved'})

    def test_video_model(self):
        # test read
        all_fields =  ['id', 'approved_categories', 'aspect_ratio', 'author',
            'categories', 'category_relationships', 'create_timestamp',
            'deleted', 'description', 'encoded_videos', 'is_ready', 'length',
            'live', 'name', 'title', 'num_views', 'owner', 'photo_url',
            'prerequisite_tasks', 'public', 'src_file_size', 'status', 'tags',
            'users_who_watched', 'version_id', 'version_label',
            'version_comment']
        manager_fields = ['id', 'approved_categories', 'author', 'categories',
            'category_relationships', 'create_timestamp', 'description',
            'encoded_videos', 'length', 'live', 'name', 'num_views',
            'photo_url', 'prerequisite_tasks', 'public', 'src_file_size',
            'status', 'tags']
        watcher_fields = ['id', 'approved_categories', 'author',
            'create_timestamp', 'description', 'encoded_videos', 'length',
            'live', 'name', 'num_views', 'photo_url', 'prerequisite_tasks',
            'public', 'src_file_size', 'tags']
        want = {
            'luser_at' : (None, None),
            'uploader_at' : (None, None),
            'cat1_watcher_at' : (set((self.video1.id,)), set(watcher_fields)),
            'cat2_watcher_at' : (None, None),
            'cat1_man_at' : (
                set((self.video1.id, self.video2.id, self.video3.id)),
                set(manager_fields)),
            'cat2_man_at' : (set((self.video1.id, self.video2.id)),
                set(manager_fields)),
        }
        for actor_at, (videos, fields) in want.iteritems():
            result = self.video_manager.get_filtered(getattr(self, actor_at),
                {}, all_fields)
            if videos:
                self.assertEqual(set(v['id'] for v in result), videos)
                for v in result:
                    self.assertEqual(set(v.keys()), fields)
            else:
                self.assertEqual(len(result), 0)
        # test category manager's ability to write metadata fields
        for actor_at in ['luser_at', 'uploader_at', 'cat1_watcher_at',
                         'cat2_watcher_at', 'cat2_man_at']:
            self.assertRaises(exceptions.PermissionDeniedException,
                self.video_manager.update, getattr(self, actor_at),
                self.video3.id,
                {'author' : 'foo', 'description' : 'bar', 'live' : True})
        self.video_manager.update(self.cat1_man_at, self.video3.id,
            {'author' : 'foo', 'description' : 'bar', 'live' : True})
        result = self.video_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : self.video3.id}},
            ['author', 'description', 'live'])[0]
        self.assertEqual(result, {
            'id' : self.video3.id,
            'author' : 'foo',
            'description' : 'bar',
            'live' : True})
        # test that category manager can't write metadata on deleted videos
        self.assertRaises(exceptions.PermissionDeniedException,
            self.video_manager.update, self.cat1_man_at, self.video4.id,
            {'author' : 'foo', 'description' : 'bar', 'live' : True})
        # test that category manager can upload new photo
        for actor_at in ['luser_at', 'uploader_at', 'cat1_watcher_at',
                         'cat2_watcher_at', 'cat2_man_at']:
            self._upload_video_photo(getattr(self, actor_at), self.video3.id,
                'biglebowski.jpg', expected_return_code=403)
        self._upload_video_photo(self.cat1_man_at, self.video3.id,
            'biglebowski.jpg')
        # test uploading videos
        self._upload_video(self.luser_at, '720x480_4.3.mov', expected_return_code=403)
        for actor_at in ['uploader_at', 'cat1_watcher_at', 'cat2_watcher_at',
                         'cat1_man_at', 'cat2_man_at']:
            self._upload_video(getattr(self, actor_at), '720x480_4.3.mov')
        # test that no-one can remove a video category relationship
        for actor_at in ['luser_at', 'uploader_at', 'cat1_watcher_at',
                         'cat2_watcher_at', 'cat1_man_at', 'cat2_man_at']:
            self.assertRaises(exceptions.PermissionDeniedException,
                self.video_manager.update, getattr(self, actor_at),
                self.video3.id, {'categories' : {'remove' : [self.cat1.id]}})
        # test that a category manager can add a video to a category they
        # don't manage in the default pending state
        for actor_at in ['luser_at', 'uploader_at', 'cat1_watcher_at',
                         'cat2_watcher_at']:
            self.assertRaises(exceptions.PermissionDeniedException,
                self.video_manager.update, getattr(self, actor_at),
                self.video3.id, {'categories' : {'add' : [self.cat2.id]}})
        self.video_manager.update(self.cat1_man_at, self.video3.id,
            {'categories' : {'add' : [self.cat2.id]}})
        result = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video3.id, 'category' : self.cat2.id}},
            ['status'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'pending')
        self.video_manager.update(self.cat2_man_at, self.video3.id,
            {'categories' : {'add' : [self.cat3.id]}})
        result = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video3.id, 'category' : self.cat3.id}},
            ['status'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'pending')
        # test that a category manager can add a video to their category
        # already in the approved state
        for actor_at in ['luser_at', 'uploader_at', 'cat1_watcher_at',
                         'cat2_watcher_at', 'cat2_man_at']:
            self.assertRaises(exceptions.PermissionDeniedException,
                self.video_manager.update, getattr(self, actor_at),
                self.video3.id, {'categories' : {
                    'add' : [{'id': self.cat4.id, 'status' : 'approved'}],
                }})
        self.video_manager.update(self.cat1_man_at, self.video3.id,
            {'categories' : {
                'add' : [{'id': self.cat4.id, 'status' : 'approved'}],
                'remove' : [],
            }})
        result = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : self.video3.id, 'category' : self.cat4.id}},
            ['status'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'approved')

    def test_encoded_video_model(self):
        all_fields = ['video', 'bitrate', 'url', 'http_url']
        want = {
            'luser_at' : None,
            'uploader_at' : None,
            'cat1_watcher_at' : set((self.video1.id,)),
            'cat2_watcher_at' : None,
            'cat1_man_at' : set((self.video1.id, self.video2.id, self.video3.id)),
            'cat2_man_at' : set((self.video1.id, self.video2.id)),
        }
        for actor_at, videos in want.iteritems():
            result = self.encoded_video_manager.get_filtered(
                getattr(self, actor_at), {}, all_fields)
            if videos:
                self.assertEqual(set(ev['video'] for ev in result), videos)
                for r in result:
                    self.assertEqual(set(r.keys()),
                        set(('id', 'video', 'bitrate', 'url')))
            else:
                self.assertEqual(len(result), 0)

    def test_video_assignment(self):
        for actor_at in ['cat1_watcher_at', 'cat1_man_at', 'cat2_man_at']:
            self.assignment_manager.create(getattr(self, actor_at),
                self.video1.id)
        self.assignment_manager.create(self.cat1_man_at, self.video2.id)
        for actor_at in ['luser_at', 'uploader_at', 'cat2_watcher_at']:
            self.assertRaises(exceptions.PermissionDeniedException,
                self.assignment_manager.create, getattr(self, actor_at),
                self.video1.id)
        self.assertRaises(exceptions.PermissionDeniedException,
            self.assignment_manager.create, self.cat2_man_at,
            self.video3.id)
        self.assertRaises(exceptions.PermissionDeniedException,
            self.assignment_manager.create, self.cat1_man_at,
            self.video4.id)

    def test_video_session_model(self):
        # test combined assignment creation/seesion creation permissions
        for actor_at in ['cat1_watcher_at', 'cat1_man_at', 'cat2_man_at']:
            self.video_session_manager.register_video_view(
                getattr(self, actor_at), self.video1.id)
        for actor_at in ['luser_at', 'uploader_at', 'cat2_watcher_at']:
            self.assertRaises(exceptions.PermissionDeniedException,
                self.video_session_manager.register_video_view,
                getattr(self, actor_at), self.video1.id)
        # test that only the owner of an assignment can create a sesion for it
        aid = self.assignment_manager.create(self.cat1_watcher_at,
            self.video1.id).id
        self.video_session_manager.create(self.cat1_watcher_at, aid)
        for actor_at in ['luser_at', 'uploader_at', 'cat2_watcher_at',
                'cat1_man_at', 'cat2_man_at']:
            self.assertRaises(exceptions.PermissionDeniedException,
                self.video_session_manager.create, getattr(self, actor_at), aid)


class TestVODACLCRUD(TestACLCRUD):
    def setUp(self):
        self.initial_setup_args = ['precor']
        super(TestVODACLCRUD, self).setUp()

    def test_acl_crud(self):
        self.do_test()


# vim:tabstop=4 shiftwidth=4 expandtab
