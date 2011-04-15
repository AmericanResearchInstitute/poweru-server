#!/usr/bin/env python
# -*- coding: utf-8 -*-
# RPC Client Test Suite
#
# A test suite for the RPC client services (typically using AMF).
#
# To use it in "remote" mode, you will need to start an instance of the Django
# server, and configure at least the SVC_TEST_HOST and SVC_TEST_PORT settings
# in either tests_svc_settings.py or your local_settings.py to point to the
# running instance.
#
# To run it in "local" mode, include the pr_svc_tests app in INSTALLED_APPS and
# run the normal unit tests.

from __future__ import with_statement

from datetime import date, datetime, timedelta
import codecs
import cPickle
import os
import pycurl
import shutil
import signal
import sys
import tempfile
import time
import urllib
import urllib2

# make stdout and stderr use UTF-8 encoding so that printing out
# UTF-8 data while debugging doesn't choke
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
sys.stderr = codecs.getwriter('utf-8')(sys.stderr)

# These imports and manglings are for "cheating" by
# using pr_services code directly.  Here's what
# we use it for:
# (1) the pr_services.pr_time module
from django.conf import settings
from django.core.management import call_command
import facade
import pr_services.pr_time

import django.db
from django.db import transaction

# Configure settings and base TestCase classes as appropriate for remote or
# local mode.
settings.SVC_TEST = getattr(settings, 'SVC_TEST', 'amf')
settings.SVC_TEST_HOST = getattr(settings, 'SVC_TEST_HOST', '127.0.0.1')
settings.SVC_TEST_PORT = getattr(settings, 'SVC_TEST_PORT', 8888)
settings.SVC_TEST_PATH = getattr(settings, 'SVC_TEST_PATH', '')
settings.SVC_TEST_URL = getattr(settings, 'SVC_TEST_URL',
    'http://%s:%d/%s%s/' % (settings.SVC_TEST_HOST, settings.SVC_TEST_PORT,
                            settings.SVC_TEST_PATH, settings.SVC_TEST))
if getattr(settings, 'SVC_TEST_REMOTE', False):
    import unittest
    BaseTestCase = unittest.TestCase
else:
    from .tests import RpcTestCase
    class BaseTestCase(RpcTestCase):
        def setUp(self):
            super(BaseTestCase, self).setUp()
            settings.SVC_TEST_HOST = self.address
            settings.SVC_TEST_PORT = self.port
            settings.SVC_TEST_URL = 'http://%s:%d/%s%s/' % (settings.SVC_TEST_HOST,
                settings.SVC_TEST_PORT, settings.SVC_TEST_PATH, settings.SVC_TEST)

class TestCase(BaseTestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        initialize_db()
        self.svcGateway = svcGateway(service=settings.SVC_TEST, url=settings.SVC_TEST_URL)
        self.setup_managers()
        self.admin_token = self.user_manager.login('admin', 'admin')['value']['auth_token']
        self.admin_user_id = self.user_manager.get_authenticated_user(self.admin_token)['value']['id']
        self.right_now = datetime.utcnow().replace(microsecond=0, tzinfo=pr_services.pr_time.UTC())
        self.one_day = timedelta(days = 1)
        self.organization1 = self.organization_manager.create(self.admin_token, 'Organization 1')['value']['id']

    def tearDown(self):
        super(TestCase, self).tearDown()

    def setup_managers(self):
        self.achievement_manager = self.svcGateway.getService('AchievementManager')
        self.answer_manager = self.svcGateway.getService('AnswerManager')
        self.assignment_manager = self.svcGateway.getService('AssignmentManager')
        self.backend_info = self.svcGateway.getService('BackendInfo')
        self.credential_manager = self.svcGateway.getService('CredentialManager')
        self.credential_type_manager = self.svcGateway.getService('CredentialTypeManager')
        self.domain_affiliation_manager = self.svcGateway.getService('DomainAffiliationManager')
        self.domain_manager = self.svcGateway.getService('DomainManager')
        self.encoded_video_manager = self.svcGateway.getService('EncodedVideoManager')
        self.event_manager = self.svcGateway.getService('EventManager')
        self.exam_manager = self.svcGateway.getService('ExamManager')
        self.exam_session_manager = self.svcGateway.getService('ExamSessionManager')
        self.group_manager = self.svcGateway.getService('GroupManager')
        self.note_manager = self.svcGateway.getService('NoteManager')
        self.organization_manager = self.svcGateway.getService('OrganizationManager')
        self.payment_manager = self.svcGateway.getService('PaymentManager')
        self.product_line_manager = self.svcGateway.getService('ProductLineManager')
        self.purchase_order_manager = self.svcGateway.getService('PurchaseOrderManager')
        self.question_manager = self.svcGateway.getService('QuestionManager')
        self.question_pool_manager = self.svcGateway.getService('QuestionPoolManager')
        self.rating_manager = self.svcGateway.getService('RatingManager')
        self.region_manager = self.svcGateway.getService('RegionManager')
        self.report_generator = self.svcGateway.getService('ReportGenerator')
        self.role_manager = self.svcGateway.getService('RoleManager')
        self.room_manager = self.svcGateway.getService('RoomManager')
        self.sco_manager = self.svcGateway.getService('ScoManager')
        self.sco_session_manager = self.svcGateway.getService('ScoSessionManager')
        self.session_manager = self.svcGateway.getService('SessionManager')
        self.session_reminder_chg_cfg_manager = self.svcGateway.getService('SessionReminderChgCfgManager')
        self.session_template_manager = self.svcGateway.getService('SessionTemplateManager')
        self.session_template_user_role_requirement_manager = self.svcGateway.getService('SessionTemplateUserRoleRequirementManager')
        self.session_user_role_manager = self.svcGateway.getService('SessionUserRoleManager')
        self.session_user_role_requirement_manager = self.svcGateway.getService('SessionUserRoleRequirementManager')
        self.task_manager = self.svcGateway.getService('TaskManager')
        self.user_manager = self.svcGateway.getService('UserManager')
        self.utils_manager = self.svcGateway.getService('UtilsManager')
        self.venue_manager = self.svcGateway.getService('VenueManager')
        self.video_manager = self.svcGateway.getService('VideoManager')
        self.video_session_manager = self.svcGateway.getService('VideoSessionManager')

    def create_instructor(self, username='instructor', title='Ms.', first_name='Teaching', last_name='Instructor', label='1234 Test Address Lane', locality='Testville',
            region='NC', postal_code='12345', country='US', phone='378-478-3845'):
        username = self.user_manager.generate_username('', first_name, last_name)['value']
        email = username+'@electronsweatshop.com'
        shipping_address = {'label' : label, 'locality' : locality, 'postal_code' : postal_code, 'country' : country, 'region' : region}
        billing_address = {'label' : label, 'locality' : locality, 'postal_code' : postal_code, 'country' : country, 'region' : region}
        instructor_group_id = self.group_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Instructors'}})['value'][0]['id']
        instructor_id = self.user_manager.create(self.admin_token, username, 'password', title, first_name, last_name, phone, email, 'active',
            {'shipping_address' : shipping_address, 'billing_address' : billing_address, 'groups' : [instructor_group_id]})['value']['id']
        instructor_at = self.user_manager.login(username, 'password')['value']['auth_token']
        return instructor_id, instructor_at

    def create_korean_user(self, username='korean', title='Mr.', first_name='Korean', last_name='Guy', label='1234 Test Address Lane', locality='Testville',
            region='NC', postal_code='12345', country='US', phone='378-478-3845'):
        # Let's create a user who prefers to work in Korean
        username = self.user_manager.generate_username('', first_name, last_name)['value']
        email = username+'@electronsweatshop.com'
        shipping_address = {'label' : label, 'locality' : locality, 'postal_code' : postal_code, 'country' : country, 'region' : region}
        billing_address = {'label' : label, 'locality' : locality, 'postal_code' : postal_code, 'country' : country, 'region' : region}
        korean_user_id = self.user_manager.create(self.admin_token, username, 'password', title, first_name, last_name, phone, email, 'active',
            {'lang' : 'kor', 'shipping_address' : shipping_address, 'billing_address' : billing_address})['value']['id']
        korean_user_at = self.user_manager.login(username, 'password')['value']['auth_token']
        return korean_user_id, korean_user_at

    def create_student(self, username='student', title='Private', first_name='Learning', last_name='Student', label='1234 Test Address Lane', locality='Testville',
            region='NC', postal_code='12345', country='US', phone='378-478-3845'):
        username = self.user_manager.generate_username('', first_name, last_name)['value']
        email = username+'@electronsweatshop.com'
        shipping_address = {'label' : label, 'locality' : locality, 'postal_code' : postal_code, 'country' : country, 'region' : region}
        billing_address = {'label' : label, 'locality' : locality, 'postal_code' : postal_code, 'country' : country, 'region' : region}
        student_group_id = self.group_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Students'}})['value'][0]['id']
        student_id = self.user_manager.create(self.admin_token, username, 'password', title, first_name, last_name, phone, email, 'active',
            {'shipping_address' : shipping_address, 'billing_address' : billing_address, 'groups' : [student_group_id]})['value']['id']
        student_at = self.user_manager.login(username, 'password')['value']['auth_token']
        return student_id, student_at

    def create_unprivileged_user(self, username='unprivileged', title='Mr.', first_name='Unprivileged', last_name='User', label='1234 Test Address Lane',
            locality='Testville', region='NC', postal_code='12345', country='US', phone='378-478-3845'):
        username = self.user_manager.generate_username('', first_name, last_name)['value']
        email = username+'@electronsweatshop.com'
        shipping_address = {'label' : label, 'locality' : locality, 'postal_code' : postal_code, 'country' : country, 'region' : region}
        billing_address = {'label' : label, 'locality' : locality, 'postal_code' : postal_code, 'country' : country, 'region' : region}
        user_id = self.user_manager.create(self.admin_token, username, 'password', title, first_name, last_name, phone, email, 'active',
            {'shipping_address' : shipping_address, 'billing_address' : billing_address})['value']['id']
        user_at = self.user_manager.login(username, 'password')['value']['auth_token']
        return user_id, user_at

################################################################################################################################################
#
# Let the unit tests begin!
#
################################################################################################################################################

class TestAssignmentManagerSvc(TestCase):
    def test_get_filtered(self):
        ret = self.assignment_manager.get_filtered(self.admin_token, {}, [])
        self.assertEquals(ret['status'], 'OK')
        self.assertTrue(isinstance(ret['value'], list))

class TestBackendInfoSvc(TestCase):
    def test_backend_info(self):
        ret = self.backend_info.get_time_zone()
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'], settings.TIME_ZONE)
        ret = self.backend_info.get_current_timestamp()
        self.assertEquals(ret['status'], 'OK')
        from pr_services.iso8601 import parse
        t1 = parse(ret['value'])
        t2 = time.mktime(datetime.now().timetuple())
        self.assertTrue((t2 - t1) < 10.0)
        ret = self.backend_info.get_revision()
        self.assertEquals(ret['status'], 'OK')
        self.assertTrue(ret['value'])

class TestCredentialSystem(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_create(self):
        ret = self.user_manager.create(self.admin_token, 'rpbarlow', 'topSecret', 'Mr.', 'Randy', 'Barlow',
            '919-816-2352', 'rbarlow@americanri.com', 'active')
        self.assertEquals(ret['status'], 'OK')
        u = ret['value']
        ret = self.credential_type_manager.create(self.admin_token, 'B.S.',
            'Electrical Engineering')
        self.assertEquals(ret['status'], 'OK')
        ctyp1 = ret['value']
        ret = self.credential_manager.create(self.admin_token, u['id'], 
            ctyp1['id'], {'serial_number' : '12345', 'date_granted' : '2008-06-12',
            'date_expires' : '2009-06-12T16:51Z'})
        self.assertEquals(ret['status'], 'OK')
        cred = ret['value']
        ret = self.credential_manager.get_filtered(self.admin_token, {},
            ['credential_type', 'id', 'user'])
        self.assertEquals(ret['status'], 'OK')
        creds = ret['value']
        self.assertEquals(len(creds), 1)
        self.assertEquals(creds[0]['user'], int(u['id']))
        self.assertEquals(creds[0]['credential_type'], int(ctyp1['id']))

    def test_credential_granting(self):
        """
        We are going to do a fairly general test on the credential system in which a user must
        take two scorm courses and an exam.  We will test to make sure that credentials can be
        granted in this way.
        """
        ctype_id = self.credential_type_manager.create(self.admin_token, 'Constant Contacter',
            'Constant Contact Constant Contacter')['value']['id']
        scorm_zip_file_1_name = os.path.join(os.path.dirname(__file__), '..',
            'test_services/ConstantCon1.zip')
        with open(scorm_zip_file_1_name, 'r') as scorm_zip_file:
            # For some reason we want to use to use a private method on the
            # ScoManager(), which isn't exposed via RPC.  So we cheat, and get
            # direct access to the actual manager from the facade.
            facade.managers.ScoManager()._process_scorm_file(self.admin_token, scorm_zip_file)
        scorm_zip_file_2_name = os.path.join(os.path.dirname(__file__), '..',
            'test_services/ConstantCon2.zip')
        with open(scorm_zip_file_2_name, 'r') as scorm_zip_file:
            # Here we are, cheating again.
            facade.managers.ScoManager()._process_scorm_file(self.admin_token, scorm_zip_file)
        # Let's make the first sco a prerequisite for the second
        ret = self.sco_manager.update(self.admin_token, 2, {'prerequisite_tasks' : [1]})
        # Let's create an exam with one question with a prerequisite of visiting the second SCO
        exam_id = self.exam_manager.create(self.admin_token, 'worthiness_test',
            'Worthiness Test', {'passing_score': 100, 'prerequisite_tasks': [2]})['value']['id']
        question_pool_id = self.question_pool_manager.create(self.admin_token,
            exam_id, 'Worthiness')['value']['id']
        question_id = self.question_manager.create(self.admin_token, question_pool_id,
            'choice', 'Are you prepared to annoy the heck out of everyone?',
            {'rejoinder' : 'Then you shall die!'})['value']['id']
        a1_id = self.answer_manager.create(self.admin_token, question_id, 'Yes!',
            {'correct' : True})['value']['id']
        a2_id = self.answer_manager.create(self.admin_token, question_id,
            'No, I\'m lame')['value']['id']
        ret = self.achievement_manager.create(self.admin_token, 'Awesome', '')
        self.assertEquals(ret['status'], 'OK')
        achievement_id = ret['value']['id']
        ret = self.exam_manager.update(self.admin_token, exam_id, {'achievements' : [achievement_id]})
        self.assertEquals(ret['status'], 'OK')
        the_scos = self.sco_manager.get_filtered(self.admin_token, {})['value']
        the_task_ids = [exam_id]
        for sco in the_scos:
            the_task_ids.append(sco['id'])
        # Let's set these two Scos to be the two required tasks for the credential_type we made
        # earlier
        ret = self.credential_type_manager.update(self.admin_token, ctype_id,
            {'required_achievements' : [achievement_id]})
        self.assertEquals(ret['status'], 'OK')
        # Let's assign a credential to a user.
        student_id, student_at = self.create_student()
        cc_cred_id = self.credential_manager.create(self.admin_token, student_id,
            ctype_id)['value']['id']
        cc_cred = self.credential_manager.get_filtered(student_at,
            {'exact' : {'id' : cc_cred_id}}, ['status'])['value'][0]
        self.assertEquals(cc_cred['status'], 'pending')
        # Let's have the user visit the first sco
        sco_1 = self.sco_manager.get_filtered(student_at, {}, ['url'])['value'][0]
        # This Sco just has to be visited to be marked completed, so let's visit it and ensure
        # that we get marked as completed
        assignment_id = self.assignment_manager.create(self.admin_token, sco_1['id'], student_id)['value']['id']
        the_url = 'http://' + settings.SVC_TEST_HOST + ':' + \
            str(settings.SVC_TEST_PORT) + sco_1['url']
        course = urllib.urlopen(the_url)
        ret = self.assignment_manager.get_filtered(self.admin_token, {'exact' : {'id' : assignment_id}}, ['status'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['status'], 'completed')
        # The user hasn't visited the second sco yet, so this should still be pending
        cc_cred = self.credential_manager.get_filtered(student_at,
            {'exact' : {'id' : cc_cred_id}}, ['status'])['value'][0]
        self.assertEquals(cc_cred['status'], 'pending')
        # Let's have the user attempt to take the exam.  Since the prerequisites of the exam
        # haven't been met, this should raise a permission denied exception
        assignment_id = self.assignment_manager.create(self.admin_token, exam_id, student_id)['value']['id']
        ret = self.exam_session_manager.create(student_at, assignment_id, True)
        self.assertEquals(ret['error'][0], 23) #Permission denied
        # Let's visit the second sco now
        sco_2 = self.sco_manager.get_filtered(student_at, {}, ['url'])['value'][1]
        # This Sco just has to be visited to be marked completed, so let's visit it and ensure
        # that we get marked as completed
        the_url = 'http://' + settings.SVC_TEST_HOST + ':' + \
            str(settings.SVC_TEST_PORT) + sco_2['url']
        assignment_id = self.assignment_manager.create(self.admin_token, sco_2['id'], student_id)['value']['id']
        course = urllib.urlopen(the_url)
        ret = self.assignment_manager.get_filtered(self.admin_token, {'exact' : {'id' : assignment_id}}, ['status'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['status'], 'completed')
        # The user has visited both scos, but not taken the exam, so the credential should be
        # marked pending still
        cc_cred = self.credential_manager.get_filtered(student_at,
            {'exact' : {'id' : cc_cred_id}}, ['status'])['value'][0]
        self.assertEquals(cc_cred['status'], 'pending')
        # Let's have the User pass the exam now
        assignment_id = self.assignment_manager.create(self.admin_token, exam_id, student_id)['value']['id']
        exam_session = self.exam_session_manager.create(student_at, assignment_id, True)['value']
        ret = self.exam_session_manager.add_response(student_at, exam_session['id'],
            question_id, {'answers' : [a1_id]})
        ret = self.exam_session_manager.finish(student_at, exam_session['id'])
        # The user has visited both scos, and taken the exam, so the credential should be
        # marked granted
        ret = self.credential_manager.get_filtered(student_at,
            {'exact' : {'id' : cc_cred_id}}, ['status', 'date_granted'])
        self.assertEquals(ret['status'], 'OK')
        cc_cred = ret['value'][0]
        self.assertEquals(len(ret['value']), 1)
        self.assertEquals(cc_cred['status'], 'granted')
        self.assertTrue('date_granted' in cc_cred)

    def test_get_filtered(self):
        u = self.user_manager.create(self.admin_token, 'rpbarlow', 'topSecret', 'Mr.', 'Randy', 'Barlow',
            '919-816-2352', 'rbarlow@americanri.com', 'active')
        ctyp1 = self.credential_type_manager.create(self.admin_token, 'B.S.',
            'Electrical Engineering')
        cred = self.credential_manager.create(self.admin_token, u['value']['id'], 
            ctyp1['value']['id'],
            {'serial_number' : '12345', 'date_granted' : '2008-06-12T16:51Z', 'date_expires' : '2009-06-12T16:51Z'})
        ret = self.credential_manager.get_filtered(self.admin_token, {'exact' : {'user' : u['value']['id']}}, ['id', 'serial_number',
            'user'])
        self.assertEquals(len(ret['value']), 1)
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['serial_number'], '12345')
        self.assertEquals(ret['value'][0]['user'], int(u['value']['id']))

    def test_permission_denied(self):
        u = self.user_manager.create(self.admin_token, 'rpbarlow', 'topSecret', 'Mr.', 'Randy', 'Barlow',
                             '919-816-2352', 'rbarlow@americanri.com', 'active')
        unauth_token = self.user_manager.login('rpbarlow', 'topSecret')['value']['auth_token']
        ctyp1 = self.credential_type_manager.create(self.admin_token, 'B.S.', 'Electrical Engineering')
        ctyp2 = self.credential_type_manager.create(self.admin_token, 'M.S.', 'Electrical Engineering')
        cred = self.credential_manager.create(unauth_token, u['value']['id'], [ctyp1['value']['id'], ctyp2['value']['id']]) 
        self.assertEquals(cred['status'], 'error')
        self.assertEquals(cred['error'][0], 23)

    def test_update(self):
        user_id = self.user_manager.create(self.admin_token, 'rbarlow', 'topSecret', 'Mr.', 'Randy', 'Barlow',
            '919-816-2352', 'rbarlow@americanri.com', 'active', {'email2' : 'randy@electronsweatshop.com'})['value']['id']
        ctyp1_id = self.credential_type_manager.create(self.admin_token, 'B.S.', 'Electrical Engineering')['value']['id']
        cred_id = self.credential_manager.create(self.admin_token, user_id, ctyp1_id,
            {'serial_number' : '1234', 'authority' : 'North Carolina State Univerity'})['value']['id']
        ret = self.credential_manager.update(self.admin_token, cred_id, {'authority' : 'Stanford University'})
        self.assertEquals(ret['status'], 'OK')
        ret = self.credential_manager.get_filtered(self.admin_token, {}, ['authority'])
        self.assertEquals(ret['value'][0]['authority'], 'Stanford University')

class TestDjango(TestCase):
    def test_transactions(self):
        super_admins_group_id = self.group_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Super Administrators'}})['value'][0]['id']
        ret = self.user_manager.create('', 'permission_denied', 'password', 'Mr.', 'Shouldn\'t', 'Exist',
            '555.555.5555', 'shouldnot@exist.com', 'pending', {'groups' : [super_admins_group_id]})
        self.assertEquals(ret['error'][0], 23) # Permission denied
        # Because permission denied happened, the user should not exist, and so shouldn't be returned by the next call:
        users = self.user_manager.get_filtered(self.admin_token, {}, ['last_name'])
        for user in users['value']:
            self.assertTrue(user['last_name'] != 'Exist')

class TestEventManagerSvc(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_facebook_message(self):
        # boilerplate so that we have things to associate with the events
        # we're going to create
        ret = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(ret['status'], 'OK')
        region1_id = ret['value']['id']
        ret = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1_id)
        self.assertEquals(ret['status'], 'OK')
        venue1_id = ret['value']['id']
        ret = self.product_line_manager.create(self.admin_token, 'A Product Line')
        self.assertEquals(ret['status'], 'OK')
        a_product_line_id = ret['value']['id']

        # create an event with a venue and not a region, as well as an external
        # reference
        ret = self.event_manager.create(self.admin_token, 'EVT', 'Best Title Ever',
            'Described!', self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id,
            {'venue' : venue1_id, 'external_reference' : u'xyz123'})
        self.assertEquals(ret['status'], 'OK')
        event1_id = ret['value']['id']
        ret = self.event_manager.get_filtered(self.admin_token, {'exact': {'title' : 'Best Title Ever'}}, ['facebook_message']) 
        self.assertEquals(ret['value'][0]['facebook_message'], 'I just signed up for Best Title Ever! Click the link to join me.')

    def test_twitter_message(self):
        # boilerplate so that we have things to associate with the events
        # we're going to create
        ret = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(ret['status'], 'OK')
        region1_id = ret['value']['id']
        ret = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1_id)
        self.assertEquals(ret['status'], 'OK')
        venue1_id = ret['value']['id']
        ret = self.product_line_manager.create(self.admin_token, 'A Product Line')
        self.assertEquals(ret['status'], 'OK')
        a_product_line_id = ret['value']['id']

        # create an event with a venue and not a region, as well as an external
        # reference
        ret = self.event_manager.create(self.admin_token, 'EVT', 'Best Title Ever',
            'Described!', self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id,
            {'venue' : venue1_id, 'external_reference' : u'xyz123'})
        self.assertEquals(ret['status'], 'OK')
        event1_id = ret['value']['id']
        ret = self.event_manager.get_filtered(self.admin_token, {'exact': {'title' : 'Best Title Ever'}}, ['twitter_message']) 
        self.assertEquals(ret['value'][0]['twitter_message'], 'I just signed up for Best Title Ever! Join me! ')

    def test_create(self):
        # boilerplate so that we have things to associate with the events
        # we're going to create
        ret = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(ret['status'], 'OK')
        region1_id = ret['value']['id']
        ret = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1_id)
        self.assertEquals(ret['status'], 'OK')
        venue1_id = ret['value']['id']
        ret = self.product_line_manager.create(self.admin_token, 'A Product Line')
        self.assertEquals(ret['status'], 'OK')
        a_product_line_id = ret['value']['id']
        
        # create an event with a venue and not a region, as well as an external
        # reference
        ret = self.event_manager.create(self.admin_token, 'EVT', 'Title 1',
            'Description 1', self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id,
            {'venue' : venue1_id, 'external_reference' : u'xyz123'})
        self.assertEquals(ret['status'], 'OK')
        event1_id = ret['value']['id']
        
        # create an event with a region but not a venue
        ret = self.event_manager.create(self.admin_token, 'EVT', 'Title 2',
            'Description 2 -- with a region instead of a venue', self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id, {'region' : region1_id})
        self.assertEquals(ret['status'], 'OK')
        event2_id = ret['value']['id']
        
        # create a session in one of the events
        ret = self.session_manager.create(self.admin_token, self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), 'active', True, 100, event1_id, {'modality' : 'ILT'})
        self.assertEquals(ret['status'], 'OK')
        a_product_line_session_id = ret['value']['id']

        ret = self.event_manager.get_filtered(self.admin_token, {},
            ['id', 'external_reference', 'region', 'start', 'end', 'venue',
             'sessions', 'title', 'description', 'name', 'status'])
        self.assertEquals(ret['status'], 'OK')
        events = ret['value']
        self.assertEquals(len(events), 2)
        found_event_1 = False
        found_event_2 = False
        for event in events:
            if event['id'] == int(event1_id):
                found_event_1 = True
                self.assertEquals(event['name'], 'EVT%d' % (event['id']))
                self.assertEquals(event['title'], 'Title 1')
                self.assertEquals(event['description'], 'Description 1')
                self.assertEquals(event['start'], self.right_now.date().isoformat())
                self.assertEquals(event['end'], (self.right_now+self.one_day).date().isoformat())
                self.assertEquals(event['venue'], int(venue1_id))
                self.assertEquals(event['region'], None)
                self.assertEquals(event['status'], 'active')
                self.assertEquals(event['sessions'], [int(a_product_line_session_id)])
                self.assertEquals(event['external_reference'], u'xyz123')
            elif event['id'] == int(event2_id):
                found_event_2 = True
                self.assertEquals(event['name'], 'EVT%d' % (event['id']))
                self.assertEquals(event['title'], 'Title 2')
                self.assertEquals(event['description'],
                    'Description 2 -- with a region instead of a venue')
                self.assertEquals(event['start'], self.right_now.date().isoformat())
                self.assertEquals(event['end'], (self.right_now+self.one_day).date().isoformat())
                self.assertEquals(event['venue'], None)
                self.assertEquals(event['region'], int(region1_id))
                self.assertEquals(event['sessions'], [])
        self.failUnless(found_event_1)
        self.failUnless(found_event_2)

    def test_create_events_in_the_past(self):
        """
        We don't want anyone to be able to create events that are in the past, though we will want them to be able to edit them.
        """
        ret = self.product_line_manager.create(self.admin_token, 'A Product Line')
        self.assertEquals(ret['status'], 'OK')
        a_product_line_id = ret['value']['id']
        
        # create an event with a venue and not a region, as well as an external
        # reference
        ret = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1',
            'Description 1', '2007-05-20', '2030-05-21', self.organization1, a_product_line_id)
        self.assertEquals(ret['status'], 'error') # Can't create events in the past
        self.assertEquals(ret['error'][0], 121) # Validation error
        event = self.event_manager.create(self.admin_token, 'About to happen', 'Seriously, you\'re almost late, so hurry up!', 'What are you waiting for?', self.right_now.isoformat(),
            self.right_now.isoformat(), self.organization1, a_product_line_id)
        self.assertEquals(event['status'], 'OK')
        time.sleep(1)
        ret = self.event_manager.update(self.admin_token, event['value']['id'], {'title' : 'Whoops, you missed it!'})
        self.assertEquals(ret['status'], 'OK')
        ret = self.event_manager.update(self.admin_token, event['value']['id'], {'start' : (self.right_now - self.one_day*2).isoformat()})
        self.assertEquals(ret['status'], 'error') # Can't set the event to be in the past
        self.assertEquals(ret['error'][0], 121) # Validation error
        ret = self.event_manager.update(self.admin_token, event['value']['id'], {'start' : (self.right_now - self.one_day).isoformat()})
        self.assertEquals(ret['status'], 'OK') # We allow users to set the event to yesterday since we're storing UTC and we aren't translating from their locale

class TestExams(TestCase):
    def test_all(self):
        ret = self.exam_manager.create(self.admin_token, 'answers_questions_and_rate_the_admin', 'Answer Questions and rate the admin', {'passing_score' : 80})
        self.assertEquals(ret['status'], 'OK')
        exam_id = ret['value']['id']
        
        ret = self.question_pool_manager.create(self.admin_token, exam_id, 'Question Pool Title', {'name': 'question_pool'})
        self.assertEquals(ret['status'], 'OK')
        qp_id = ret['value']['id']
        
        ret = self.question_manager.create(self.admin_token, qp_id, 'choice', 'What color is the sky?',
            {'rejoinder' : 'Idiot!'})
        q1_id = ret['value']['id']
        ret = self.answer_manager.create(self.admin_token, q1_id, 'Red')
        self.assertEquals(ret['status'], 'OK')
        a1_id = ret['value']['id']
        ret = self.answer_manager.create(self.admin_token, q1_id, 'Blue', {'correct' : True})
        self.assertEquals(ret['status'], 'OK')
        a2_id = ret['value']['id']
        ret = self.answer_manager.create(self.admin_token, q1_id, 'Green')
        self.assertEquals(ret['status'], 'OK')
        a3_id = ret['value']['id']
        self.assertEquals(ret['status'], 'OK')
        
        ret = self.question_manager.create(self.admin_token, qp_id, 'choice', 'What color is a banana?',
            {'rejoinder' : 'Idiot!', 'text_response': True})
        self.assertEquals(ret['status'], 'OK')
        q2_id = ret['value']['id']
        ret = self.answer_manager.create(self.admin_token, q2_id, 'Yellow', {'correct' : True})
        self.assertEquals(ret['status'], 'OK')
        a4_id = ret['value']['id']
        ret = self.answer_manager.create(self.admin_token, q2_id, 'Blue')
        self.assertEquals(ret['status'], 'OK')
        a5_id = ret['value']['id']
        ret = self.answer_manager.create(self.admin_token, q2_id, 'Green')
        self.assertEquals(ret['status'], 'OK')
        a6_id = ret['value']['id']
        
        ret = self.question_manager.create(self.admin_token, qp_id, 'rating', 'How cool are you?',
             {'min_value': 0, 'max_value': 5 })
        self.assertEquals(ret['status'], 'OK')
        r1_id = ret['value']['id']
        ret = self.question_manager.create(self.admin_token, qp_id, 'rating', 'How cool am I?',
            {'min_value': 0, 'max_value': 5, 'text_response': True})
        self.assertEquals(ret['status'], 'OK')
        r2_id = ret['value']['id']

        assignment_id = self.assignment_manager.create(self.admin_token, exam_id)['value']['id']
        ret = self.exam_session_manager.create(self.admin_token, assignment_id, True)
        self.assertEquals(ret['status'], 'OK')
        exam_session = ret['value']
        self.assertEquals('id' in exam_session, True)
        self.assertEquals('question_pools' in exam_session, True)
        self.assertEquals(len(exam_session['question_pools']), 1)

        ret = self.exam_session_manager.add_response(self.admin_token, exam_session['id'], q1_id,
                {'answers' : [a3_id]})
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value']['rejoinder'], 'Idiot!')
        ret = self.exam_session_manager.add_response(self.admin_token, exam_session['id'], q2_id,
                {'answers' : [a4_id], 'text' : 'Does anyone read these things?'})
        self.assertEquals(ret['status'], 'OK')
        self.assertTrue('rejoinder' not in ret['value'])
        ret = self.exam_session_manager.add_response(self.admin_token, exam_session['id'], r1_id,
            {'value': 5})
        self.assertEquals(ret['status'], 'OK')
        ret = self.exam_session_manager.add_response(self.admin_token, exam_session['id'], r2_id,
                {'value': 1, 'text' : 'You stink.'})
        self.assertEquals(ret['status'], 'OK')
        ret = self.exam_session_manager.finish(self.admin_token, exam_session['id'])
        self.assertEquals(ret['status'], 'OK')

        ret = self.exam_session_manager.get_filtered(self.admin_token, {'exact' : {'id' : exam_session['id']}}, ['id', 'score', 'response_questions'])
        self.assertEquals(ret['status'], 'OK')
        result = ret['value']
        self.assertEquals(len(result[0]['response_questions']), 4)
        # we get '50' with Sqlite and '50.00' with MySQL
        self.failUnless(result[0]['score'] in ('50', '50.00'))

        # Test get_results
        ret = self.exam_session_manager.get_results(self.admin_token, exam_session['id'])
        self.assertEquals(ret['status'], 'OK')
        results = ret['value']
        self.assertTrue('score' in results)
        # we get '50' with Sqlite and '50.00' with MySQL
        self.failUnless(results['score'] in ('50', '50.00'))
        self.assertTrue('passed' in results)
        self.assertTrue(not results['passed'])
        self.assertTrue('missed_questions' in results)
        self.assertEquals(len(results['missed_questions']), 1)
        self.assertEquals(results['missed_questions'][0]['label'], 'What color is the sky?')
        self.assertEquals(results['missed_questions'][0]['rejoinder'], 'Idiot!')

class TestGroupManagerSvc(TestCase):
    def test_group_manager_permissions(self):
        group_of_groupies_id = self.group_manager.create(self.admin_token, 'group_of_groupies')['value']['id']
        ret = self.user_manager.create(self.admin_token, 'groupie_1', 'iMAGroupie', 'Ms.', 'I\'m', 'A Groupie', '111.111.1111', 'ima@groupie.com',
            'active')
        self.assertEquals(ret['status'], 'OK')
        groupie_1_id = ret['value']['id']
        groupie_b_id = self.user_manager.create(self.admin_token, 'groupie_b', 'im2Groupie', 'Ms.', 'I\'m 2', 'Groupie',
            '222.222.2222', 'im2@groupie.com', 'active')['value']['id']
        groupie_manager_id = self.user_manager.create(self.admin_token, 'groupie_manager', 'p', 'Lord', 'Of the', 'Groupies',
            '333.333.3333', 'manager@groupie.com', 'active')['value']['id']
        ret = self.group_manager.update(self.admin_token, group_of_groupies_id, {'managers' : [groupie_manager_id]})
        manager_auth_token = self.user_manager.login('groupie_manager', 'p')['value']['auth_token']
        ret = self.group_manager.update(manager_auth_token, group_of_groupies_id, {'users' : {'add' : [groupie_1_id, groupie_b_id]}})
        ret = self.group_manager.get_filtered(manager_auth_token, {'exact' : {'id' : group_of_groupies_id}}, ['users'])
        self.assertEquals(len(ret['value'][0]['users']), 2)
        ret = self.group_manager.update(self.admin_token, group_of_groupies_id, {'users' : {'remove' : [groupie_b_id]}})
        self.assertEquals(ret['status'], 'OK')
        ret = self.group_manager.get_filtered(manager_auth_token, {'exact' : {'id' : group_of_groupies_id}}, ['users'])
        self.assertEquals(len(ret['value'][0]['users']), 1)
        self.assertEquals(ret['value'][0]['users'][0], int(groupie_1_id))

    def test_update(self):
        unprivileged_user_id, unprivileged_at = self.create_unprivileged_user()
        group_id = self.group_manager.create(self.admin_token, 'Sweep uppers')['value']['id']
        res = self.group_manager.update(unprivileged_at, group_id, {'name' : 'a longer name'})
        self.assertEquals(res['status'], 'error')
        self.assertEquals(res['error'][0], 23)
        res = self.group_manager.update(self.admin_token, group_id, {'name' : 'Sweep It Uppers'})
        self.assertEquals(res['status'], 'OK')
        ret = self.group_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Sweep It Uppers'}}, ['name'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        group_values = ret['value'][0]
        self.assertEquals(group_values['name'], 'Sweep It Uppers')
        # Test adding people to the group
        sweep_it_up_id = self.user_manager.create(self.admin_token, 'sweep_it_up', 'iSweepEveryDay', '', '', '', '', '', 'active')['value']['id']
        lay_it_down_id = self.user_manager.create(self.admin_token, 'lay_it_down', 'iLayItDown', '', '', '', '', '', 'active')['value']['id']
        ret = self.group_manager.update(unprivileged_at, group_id, {'users' : {'add' : [sweep_it_up_id, lay_it_down_id]}})
        self.assertEquals(ret['status'], 'error')
        self.assertEquals(ret['error'][0], 23) # permission denied exception
        ret = self.group_manager.update(self.admin_token, group_id, {'users' : {'add' : [sweep_it_up_id, lay_it_down_id]}})
        self.assertEquals(ret['status'], 'OK')
        ret = self.group_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Sweep It Uppers'} }, ['users'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        cool_group_values = ret['value'][0]
        self.assertEquals(len(cool_group_values['users']), 2)
        self.failUnless(int(sweep_it_up_id) in cool_group_values['users'])
        self.failUnless(int(lay_it_down_id) in cool_group_values['users'])

class TestNoteManagerSvc(TestCase):
    def test_get_notes(self):
        poo_shovelor_note = self.note_manager.create(self.admin_token,
            'This role is to grant especially smelly privileges to an unlucky subset of users.')['value']['id']
        poo_shovelor_id = self.role_manager.create(self.admin_token, 'Poo Shovelor')['value']['id']
        ret = self.role_manager.update(self.admin_token, poo_shovelor_id, {'notes' : {'add' : [poo_shovelor_note]}})
        self.assertEquals(ret['status'], 'OK')
        ret = self.role_manager.get_filtered(self.admin_token, {'exact' : {'id' : poo_shovelor_id}}, ['notes'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['notes'][0], int(poo_shovelor_note))
        ret = self.note_manager.get_filtered(self.admin_token, {'exact' : {'id' : ret['value'][0]['notes'][0]}}, ['text', 'create_timestamp'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['text'], 'This role is to grant especially smelly privileges to an unlucky subset of users.')

class TestPaymentManagerSvc(TestCase):
    def test_create(self):
        ret = self.purchase_order_manager.create(self.admin_token,
            {'user' : self.admin_user_id, 'training_units_purchased' : 100, 'training_units_price' : 5000})
        self.assertEquals(ret['status'], 'OK')
        po1_id = ret['value']['id']
        # This is info for an American Express gift card which has no remaining value.
        if 'ecommerce' in settings.INSTALLED_APPS:
            ret = self.payment_manager.create(self.admin_token, po1_id, 'Amex',
                '379014099768149', '1010', '5000', str(time.time()), 'Gift Card', 'Recipient',
                '170 Southport Dr. Suite 400', 'Morrisville', 'NC', '27650', 'US', '4434')    
            self.assertEquals(ret['status'], 'OK')

class TestProductManagerSvc(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.pm = self.svcGateway.getService('ProductManager')

    def test_create(self):
        p1 = self.pm.create(self.admin_token, 'XYZ456', 'Bucket', 'Holds water', 1599, 1499)
        product = self.pm.get_filtered(self.admin_token, {}, ['cost', 'price', 'sku'])
        self.assertEquals(product['status'], 'OK')
        self.assertEquals(product['value'][0]['sku'], 'XYZ456')
        self.assertEquals(product['value'][0]['price'], 1599)
        self.assertEquals(product['value'][0]['cost'], 1499)

class TestRegionManagerSvc(TestCase):
    def test_get_filtered(self):
        the_east_id = self.region_manager.create(self.admin_token, 'The East!')['value']['id']
        ret = self.region_manager.get_filtered(self.admin_token, {'exact' : {'id' : the_east_id}}, ['name'])
        self.assertEquals(ret['value'][0]['name'], 'The East!')

class TestRoleManagerSvc(TestCase):
    def test_create(self):
        role = self.role_manager.create(self.admin_token, 'dumbRole')
        self.assertEquals(role['status'], 'OK')
        role = self.role_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'dumbRole'}}, ['name'])['value']
        self.assertEquals(len(role), 1)

    def test_update(self):
        role_id = self.role_manager.create(self.admin_token, 'group12role')['value']['id']
        res = self.role_manager.update(self.admin_token, role_id, {'name' : 'rolesDontHaveGroupsAnymoreYo'})
        self.assertEquals(res['status'], 'OK')
        res = self.role_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'rolesDontHaveGroupsAnymoreYo'}})['value']
        self.assertEquals(len(res), 1)

class TestRoomManagerSvc(TestCase):
    def test_get_filtered(self):
        happy_land_id = self.region_manager.create(self.admin_token, 'Happy Land!')['value']['id']
        the_childrens_hospital_id = self.venue_manager.create(self.admin_token, 'The Children\'s Hospital', '911',
            happy_land_id)['value']['id']
        the_fear_room_id = self.room_manager.create(self.admin_token, 'The Fear Room!', the_childrens_hospital_id, 1)['value']['id']
        ret = self.room_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : the_fear_room_id}}, ['capacity', 'name'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['capacity'], 1)
        self.assertEquals(ret['value'][0]['name'], 'The Fear Room!')

class TestScoManagerSvc(TestCase):
    def test_sco_url(self):
        refresh_db()
        scorm_zip_file_name = os.path.join(os.path.dirname(__file__),  '..', 'test_services/ConstantCon1.zip')
        with open(scorm_zip_file_name, 'r') as scorm_zip_file:
            # Use local manager instance instead of RPC call.
            facade.managers.ScoManager()._process_scorm_file(self.admin_token, scorm_zip_file)
        ret = self.sco_manager.get_filtered(self.admin_token, {}, ['name', 'title',
            'url', 'course', 'completion_requirement', 'data', 'description', 'prerequisite_tasks'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['completion_requirement'], 'visit_sco')
        self.assertEquals(ret['value'][0]['name'], 'I_SCO0')
        self.assertEquals(ret['value'][0]['title'], 'The Power of Email Marketing: Getting to Know Constant Contact')
        self.assertTrue('url' in ret['value'][0])

class TestScormServer(TestCase):
    """
    This test case checks to make sure the scorm_server URL target works as expected.
    """
    def test_exception_handling(self):
        refresh_db()
        scorm_zip_file_name = os.path.join(os.path.dirname(__file__), '..', 'test_services/ConstantCon1.zip')
        with open(scorm_zip_file_name, 'r') as scorm_zip_file:
            # Use local manager instance instead of RPC call.
            facade.managers.ScoManager()._process_scorm_file(self.admin_token, scorm_zip_file)
        sco = self.sco_manager.get_filtered(self.admin_token, {}, ['url'])['value'][0]
        sco_url = sco['url']
        self.assignment_manager.create(self.admin_token, sco['id'])
        sco_url = 'http://' + settings.SVC_TEST_HOST + ':' + \
            str(settings.SVC_TEST_PORT) + sco_url
        # The following line should not fail
        course = urllib2.urlopen(sco_url)
        # The following should fail with a 404 since the request target is incorrect
        the_url = sco_url[:len(sco_url)-2]+'4/'
        try:
            urllib2.urlopen(the_url)
        except urllib2.HTTPError, e:
            self.assertEqual(e.code, 404)
        else:
            self.fail('Got OK, should have gotten 404')
        # The following should fail with a 404 since the auth_token is invalid 
        the_url = sco_url[:len(sco_url)-5] + 'z' + sco_url[len(sco_url)-5:len(sco_url)]
        try:
            urllib2.urlopen(the_url)
        except urllib2.HTTPError, e:
            self.assertEqual(e.code, 404)
        else:
            self.fail('Got OK, should have gotten 404')

class TestScoSessionManagerSvc(TestCase):
    def test_sco_session_save(self):
        # Let's create a credential type and assign it to a user and see if they can complete it!
        cc_cred_type_id = self.credential_type_manager.create(self.admin_token, 'Constant Contactor',
            'Become a Constant Contact Constant Contactor, Constantly!')['value']['id']
        scorm_zip_file_1_name = os.path.join(os.path.dirname(__file__), '..',
            'test_services/ConstantCon1.zip')
        refresh_db()
        with open(scorm_zip_file_1_name, 'r') as scorm_zip_file:
            # Use local manager instance instead of RPC call.
            facade.managers.ScoManager()._process_scorm_file(self.admin_token, scorm_zip_file)
        scorm_zip_file_2_name = os.path.join(os.path.dirname(__file__), '..',
            'test_services/ConstantCon2.zip')
        with open(scorm_zip_file_2_name, 'r') as scorm_zip_file:
            # Use local manager instance instead of RPC call.
            facade.managers.ScoManager()._process_scorm_file(self.admin_token, scorm_zip_file)
        the_scos = self.sco_manager.get_filtered(self.admin_token, {})['value']
        self.assertEquals(len(the_scos), 2)
        the_sco_ids = [sco['id'] for sco in the_scos]
        ret = self.achievement_manager.create(self.admin_token, 'Awesome Person 1', '')
        self.assertEquals(ret['status'], 'OK')
        achievement1_id = ret['value']['id']
        ret = self.achievement_manager.create(self.admin_token, 'Awesome Person 2', '')
        self.assertEquals(ret['status'], 'OK')
        achievement2_id = ret['value']['id']
        ret = self.sco_manager.update(self.admin_token, the_sco_ids[0], {'achievements' : [achievement1_id]})
        self.assertEquals(ret['status'], 'OK')
        ret = self.sco_manager.update(self.admin_token, the_sco_ids[1], {'achievements' : [achievement2_id]})
        self.assertEquals(ret['status'], 'OK')
        # Let's set these two Scos to be the two required tasks for the credential_type we made earlier
        ret = self.credential_type_manager.update(self.admin_token, cc_cred_type_id, {'required_achievements' : [achievement1_id, achievement2_id]})
        self.assertEquals(ret['status'], 'OK')
        # Let's assign a credential to a user.  We'll just use the admin user for now
        cc_cred_id = self.credential_manager.create(self.admin_token, self.admin_user_id, cc_cred_type_id)['value']['id']
        cc_cred = self.credential_manager.get_filtered(self.admin_token, {'exact' : {'user' : self.admin_user_id}}, ['status'])['value'][0]
        self.assertEquals(cc_cred['status'], 'pending')
        # Let's have the user visit the first sco
        sco_1 = self.sco_manager.get_filtered(self.admin_token, {}, ['url'])['value'][0]
        # This Sco just has to be visited to be marked completed, so let's visit it and ensure
        # that we get marked as completed
        the_url = 'http://' + settings.SVC_TEST_HOST + ':' + \
            str(settings.SVC_TEST_PORT) + sco_1['url']
        assignment = self.assignment_manager.create(self.admin_token, sco_1['id'])['value']
        course = urllib2.urlopen(the_url)
        ret = self.assignment_manager.get_filtered(self.admin_token, {'exact' : {'id' : assignment['id']}}, ['status'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['status'], 'completed')
        # The user hasn't visited the second sco yet, so this should still be pending
        cc_cred = self.credential_manager.get_filtered(self.admin_token, {'exact' : {'user' : self.admin_user_id}}, ['status'])['value'][0]
        self.assertEquals(cc_cred['status'], 'pending')
        # Let's visit the second sco now
        sco_2 = self.sco_manager.get_filtered(self.admin_token, {}, ['url'])['value'][1]
        # This Sco just has to be visited to be marked completed, so let's visit it and ensure
        # that we get marked as completed
        the_url = 'http://' + settings.SVC_TEST_HOST + ':' + \
            str(settings.SVC_TEST_PORT) + sco_2['url']
        assignment = self.assignment_manager.create(self.admin_token, sco_2['id'])['value']
        course = urllib.urlopen(the_url)
        ret = self.assignment_manager.get_filtered(self.admin_token, {'exact' : {'id' : assignment['id']}}, ['status'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['status'], 'completed')
        # The user has visited both scos, so the credential should be marked granted now
        cc_cred = self.credential_manager.get_filtered(self.admin_token, {'exact' : {'user' : self.admin_user_id}}, ['status', 'date_granted'])['value'][0]
        self.assertEquals(cc_cred['status'], 'granted')
        self.assertTrue('date_granted' in cc_cred)

class TestSecurityModule(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_expired_auth_token(self):
        u_id = u = self.user_manager.create(self.admin_token, 's', 'j', 'Mr.', 's', 'j', '1', 'd@g.com', 'active')['value']['id']
        at = self.user_manager.login('s', 'j')['value']['auth_token']
        u = self.user_manager.get_filtered(at, {'exact' : {'id' : u_id}}, ['id', 'last_name'])['value'][0]
        refresh_db()
        at = facade.models.AuthToken.objects.get(session_id = at)
        at.time_of_expiration = datetime.utcnow()-timedelta(days=1)
        at.save()
        res = self.user_manager.get_filtered(at.session_id, {'exact' : {'id' : u_id}}, ['id', 'last_name'])
        self.assertEquals(res['error'][0], 49) # Make sure the auth_token expired exception occurs

class TestSessionManagerSvc(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_create(self):
        region1 = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(region1['status'], 'OK')
        venue1 = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1['value']['id'])
        self.assertEquals(venue1['status'], 'OK')

        a_product_line_id = self.product_line_manager.create(self.admin_token, 'A Product Line')['value']['id']
        event1 = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1', 'Description 1', self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id, {'venue' : venue1['value']['id']})['value']['id']
        a_product_line_session = self.session_manager.create(self.admin_token, self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(),
            'active', True, 100, event1, {'modality' : 'ILT'})
        self.assertEquals(a_product_line_session['status'], 'OK')
        a_product_line_session_id = a_product_line_session['value']['id']
        res = self.session_manager.get_filtered(self.admin_token, {'exact' : {'id' : a_product_line_session_id}}, ['modality'])
        self.assertEquals(res['value'][0]['modality'], 'ILT')
        
        # Now make a session user role requirement for this session...
        # get the session user role first
        ret = self.session_user_role_manager.get_filtered(self.admin_token, { 'exact' : { 'name' : 'Student' } })
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        student_role_id = ret['value'][0]['id']
        # now make the requirement
        ret = self.session_user_role_requirement_manager.create(self.admin_token,
            a_product_line_session_id, student_role_id, 0, 30, False)
        self.assertEquals(ret['status'], 'OK')
        surr_id = ret['value']['id']
        # make sure that we can get the session user role requirements
        ret = self.session_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : a_product_line_session_id}}, ['session_user_role_requirements'])
        self.assertEquals(ret['status'], 'OK')
        self.failUnless(isinstance(ret['value'], list))
        self.assertEquals(len(ret['value']), 1)
        a_product_line_session = ret['value'][0]
        self.assertEquals(a_product_line_session['session_user_role_requirements'], [int(surr_id)])

    def test_filter_for_date_range(self):
        region1 = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(region1['status'], 'OK')
        venue1 = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1['value']['id'])
        self.assertEquals(venue1['status'], 'OK')
        a_product_line_id = self.product_line_manager.create(self.admin_token, 'A Product Line, Yo!')['value']['id']
        event1 = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1', 'Description 1', self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id, {'venue' : venue1['value']['id']})['value']['id']
        an_session_id = self.session_manager.create(self.admin_token, self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(), 'active',
            True, 100, event1, {'modality' : 'ILT'})['value']['id']
        res = self.session_manager.get_filtered(self.admin_token,
            {'greater_than' : {'start' : (self.right_now.date()-self.one_day).isoformat()},
            'less_than' : {'end' : (self.right_now.date()+2*self.one_day).isoformat()}}, ['name', 'status'])
        self.assertEquals(res['status'], 'OK')
        self.assertEquals(res['value'][0]['status'], 'active')

    def test_remind_invitees(self):
        region1 = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(region1['status'], 'OK')
        venue1 = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1['value']['id'])
        self.assertEquals(venue1['status'], 'OK')
        a_product_line_id = self.product_line_manager.create(self.admin_token, 'A Product Line, Woo!')['value']['id']
        event1 = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1', 'Description 1', self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id, {'venue' : venue1['value']['id']})['value']['id']
        ret = self.session_manager.create(self.admin_token, self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(), 'active', True, 100,
            event1) 
        self.assertEquals(ret['status'], 'OK')
        evt_id = ret['value']['id']

        ret = self.user_manager.create(self.admin_token, 'instructor_1', 'password', 'Mr.', 'David', 'Smith', '', 'david@example.smith.us', 'active')
        self.assertEquals(ret['status'], 'OK')
        instructor_1_id = ret['value']['id']
        ret = self.user_manager.create(self.admin_token, 'learner_1', 'password', 'Ms.', 'Josephine', 'Howard', '', 'jhoward@example.info', 'active')
        self.assertEquals(ret['status'], 'OK')
        learner_1_id = ret['value']['id']
        ret = self.user_manager.create(self.admin_token, 'learner_2', 'password', 'Mr.', 'Jon', 'Haskell', '', 'jhaskell@fake.acme.com', 'active')
        self.assertEquals(ret['status'], 'OK')
        learner_2_id = ret['value']['id']
        ret = self.user_manager.create(self.admin_token, 'learner_3', 'password', '', 'Eleanor', 'Jones', '', 'eleaner_jones@example.foo.bar.info', 'active')
        self.assertEquals(ret['status'], 'OK')
        learner_3_id = ret['value']['id']
        # both an instructor and a learner
        ret = self.user_manager.create(self.admin_token, 'instr_learner', 'password', 'Mrs.', 'Ophelia', 'Brown', '', 'ophelia.brown@npr.example.org', 'active')
        self.assertEquals(ret['status'], 'OK')
        instr_learner_id = ret['value']['id']

        ret = self.session_user_role_manager.get_filtered(self.admin_token, { 'exact' : { 'name' : 'Instructor' } })
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        instructor_role_id = ret['value'][0]['id']
        ret = self.session_user_role_manager.get_filtered(self.admin_token, { 'exact' : { 'name' : 'Student' } })
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        student_role_id = ret['value'][0]['id']

        # session user role requirements for users to fill
        ret = self.session_user_role_requirement_manager.create(self.admin_token, evt_id, instructor_role_id, 1, 2, False)
        self.assertEquals(ret['status'], 'OK')
        instructor_req_id = ret['value']['id']
        ret = self.session_user_role_requirement_manager.create(self.admin_token, evt_id, student_role_id, 1, 30, False)
        self.assertEquals(ret['status'], 'OK')
        student_req_id = ret['value']['id']
        # Make sure that 30 seats are available in the student requirement
        ret = self.session_user_role_requirement_manager.get_filtered(self.admin_token, {'exact' : {'id' : student_req_id}},
            ['remaining_capacity'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['remaining_capacity'], 30)

        # enroll the users
        ret = self.assignment_manager.bulk_create(self.admin_token, instructor_req_id, [instructor_1_id, instr_learner_id])
        self.assertEquals(ret['status'], 'OK')
        ret = self.assignment_manager.bulk_create(self.admin_token, student_req_id, [learner_1_id, learner_2_id, learner_3_id, instr_learner_id])
        self.assertEquals(ret['status'], 'OK')
        # Make sure that 26 seats are available in the student requirement
        ret = self.session_user_role_requirement_manager.get_filtered(self.admin_token, {'exact' : {'id' : student_req_id}},
            ['remaining_capacity'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['remaining_capacity'], 26)

        # make sure that the right number of users are enrolled for sanity
        ret = self.session_user_role_requirement_manager.get_filtered(self.admin_token,
            { 'exact' : { 'session' : evt_id, 'session_user_role' : instructor_role_id } }, ['users'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        self.assertEquals(len(ret['value'][0]['users']), 2)
        ret = self.session_user_role_requirement_manager.get_filtered(self.admin_token,
            { 'exact' : { 'session' : evt_id, 'session_user_role' : student_role_id } }, ['users'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        self.assertEquals(len(ret['value'][0]['users']), 4)
        ret = self.session_manager.remind_invitees(self.admin_token, evt_id)
        self.assertEquals(ret['status'], 'OK')

    def test_enroll_users(self):
        region1 = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(region1['status'], 'OK')
        venue1 = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789',
            region1['value']['id'])
        self.assertEquals(venue1['status'], 'OK')
        a_product_line_id = self.product_line_manager.create(self.admin_token, 'Guess what this is?')['value']['id']
        event1 = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1',
            'Description 1', self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id,
            {'venue' : venue1['value']['id']})['value']['id']
        ret = self.session_manager.create(self.admin_token, self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), 'active', True, 100, event1) 
        self.assertEquals(ret['status'], 'OK')
        evt_id = ret['value']['id']

        ret = self.user_manager.create(self.admin_token, 'instructor_1', 'password', 'Mr.', 'David',
            'Smith', '', 'david@example.smith.us', 'active')
        self.assertEquals(ret['status'], 'OK')
        instructor_1_id = ret['value']['id']
        ret = self.user_manager.create(self.admin_token, 'learner_1', 'password', 'Ms.', 'Josephine',
            'Howard', '', 'jhoward@example.info', 'active')
        self.assertEquals(ret['status'], 'OK')
        learner_1_id = ret['value']['id']

        ret = self.session_user_role_manager.get_filtered(self.admin_token,
            { 'exact' : { 'name' : 'Instructor' } })
        self.assertEquals(ret['status'], 'OK')
        instructor_role_id = ret['value'][0]['id']
        ret = self.session_user_role_manager.get_filtered(self.admin_token,
            { 'exact' : { 'name' : 'Student' } })
        self.assertEquals(ret['status'], 'OK')
        student_role_id = ret['value'][0]['id']

        # session user role requirements for users to fill
        ret = self.session_user_role_requirement_manager.create(self.admin_token, evt_id,
            instructor_role_id, 1, 2, False)
        self.assertEquals(ret['status'], 'OK')
        instructor_req_id = ret['value']['id']
        ret = self.session_user_role_requirement_manager.create(self.admin_token, evt_id,
            student_role_id, 1, 30, False)
        self.assertEquals(ret['status'], 'OK')
        student_req_id = ret['value']['id']

        # enroll the users
        ret = self.assignment_manager.bulk_create(self.admin_token, instructor_req_id, [instructor_1_id])
        self.assertEquals(ret['status'], 'OK')
        ret = self.assignment_manager.bulk_create(self.admin_token, student_req_id, [learner_1_id])
        self.assertEquals(ret['status'], 'OK')
        
class TestSessionTemplateManagerSvc(TestCase):
    def test_get_session_template_user_role_reqs(self):
        region1 = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(region1['status'], 'OK')
        venue1 = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1['value']['id'])
        self.assertEquals(venue1['status'], 'OK')
        a_product_line_id = self.product_line_manager.create(self.admin_token, 'A Product Line!')['value']['id']
        batman_being_id = self.session_template_manager.create(self.admin_token, 'Batman Being', 'A Course on how to be Batman', '1',
            'Don\'t fake the funk on a nasty dunk', 100, 1000, True)['value']['id']
        ret = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1', 'Description 1', self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id, {'venue' : venue1['value']['id']})
        self.assertEquals(ret['status'], 'OK')
        event1 = ret['value']['id']
        batman_session_id = self.session_manager.create(self.admin_token, self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(),
            'active', True, 100, event1, {'session_template' : batman_being_id})['value']['id']
        batman_session_user_role_id = self.session_user_role_manager.create(self.admin_token, 'Batman!')['value']['id']
        batman_session_template_user_role_requirement_id = self.session_template_user_role_requirement_manager.create(
            self.admin_token, batman_being_id, batman_session_user_role_id, 0, 10, [])['value']['id']
        res = self.session_template_manager.get_filtered(self.admin_token, {'exact' : {'id' : batman_being_id}},
            ['session_template_user_role_requirements'])
        self.assertEquals(res['status'], 'OK')
        self.assertEquals(res['value'][0]['id'], int(batman_session_template_user_role_requirement_id))
        self.assertEquals(len(res['value']), 1)

    def test_attributes(self):
        description = 'This course is intended for those who are new to Python, but have some familiarity with another programming language.'
        for i in range(255):
            description += 'Blah'
        python_coding_id = self.session_template_manager.create(self.admin_token, 'Python Coding', 'Learn to Code in Python', '1', description, 0, 5, True)['value']['id']
        ret = self.session_template_manager.get_filtered(self.admin_token, {'exact' : {'id' : python_coding_id}}, ['description'])
        self.assertEquals(ret['value'][0]['description'], description)

class TestSessionUserRoleManagerSvc(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_update(self):
        unprivileged_user_id, unprivileged_at = self.create_unprivileged_user()
        session_user_role_id = self.session_user_role_manager.create(self.admin_token, 'Sweep Upper')['value']['id']
        res = self.session_user_role_manager.update(unprivileged_at, session_user_role_id, {'name' : 'Sweep It Upper'})
        self.assertEquals(res['status'], 'error')
        self.assertEquals(res['error'][0], 23)
        res = self.session_user_role_manager.update(self.admin_token, session_user_role_id, {'name' : 'Sweep It Upper'})
        session_user_roles = self.session_user_role_manager.get_filtered(self.admin_token, {'exact' : {'id' : session_user_role_id}}, ['name'])
        self.assertEquals(session_user_roles['value'][0]['name'], 'Sweep It Upper')

class TestSessionUserRoleRequirementManagerSvc(TestCase):
    def setUp(self):
        TestCase.setUp(self)
    
    def test_create(self):
        unprivileged_user_id, unprivileged_at = self.create_unprivileged_user()
        region1 = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(region1['status'], 'OK')
        venue1 = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1['value']['id'])
        self.assertEquals(venue1['status'], 'OK')
        a_product_line_id = self.product_line_manager.create(self.admin_token, 'PL')['value']['id']
        session_user_role_id = self.session_user_role_manager.create(self.admin_token, 'Millionaire')['value']['id']
        event1 = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1', 'Description 1', self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id, {'venue' : venue1['value']['id']})['value']['id']
        session_id = self.session_manager.create(self.admin_token, self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(), 'active',
            True, 100, event1, {'modality' : 'ILT'})['value']['id']
        cred_type_id = self.credential_type_manager.create(self.admin_token, 'Being a millionaire',
            'You must be a millionaire, or you are not worthy')['value']['id']
        session_user_role_requirement = self.session_user_role_requirement_manager.create(unprivileged_at, session_id,
            session_user_role_id, 1, 10, False, [cred_type_id])
        self.assertEquals(session_user_role_requirement['status'], 'error')
        self.assertEquals(session_user_role_requirement['error'][0], 23)
        session_user_role_requirement = self.session_user_role_requirement_manager.create(self.admin_token, session_id,
            session_user_role_id, 1, 10, False, [cred_type_id])
        self.assertEquals(session_user_role_requirement['status'], 'OK')
        res = self.session_user_role_requirement_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : session_user_role_requirement['value']['id']}}, ['credential_types'])
        self.assertEquals(res['status'], 'OK')
        self.assertEquals(res['value'][0]['credential_types'][0], int(cred_type_id))

class TestTaskManagerSvc(TestCase):
    def test_create(self):
        task_1 = self.task_manager.create(self.admin_token, 'Gather Ingredients',
            'Gather all the ingredients necessary to bake a cake.')
        self.assertEquals(task_1['status'], 'error')
        self.assertEquals(task_1['error'][0], 5) # Operation Not Permitted

    def test_get_filtered(self):
        refresh_db()
        scorm_zip_file_name = os.path.join(os.path.dirname(__file__), '..', 'test_services/ConstantCon1.zip')
        with open(scorm_zip_file_name, 'r') as scorm_zip_file:
            # Use local manager instance instead of RPC call.
            facade.managers.ScoManager()._process_scorm_file(self.admin_token, scorm_zip_file)
        ret = self.task_manager.get_filtered(self.admin_token, {}, ['content_type', 'name', 'title'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'][0]['content_type'], 'pr_services.sco')
        self.assertEquals(ret['value'][0]['name'], 'I_SCO0')
        self.assertEquals(ret['value'][0]['title'], 'The Power of Email Marketing: Getting to Know Constant Contact')

class TestUserManagerSvc(TestCase):
    def test_domain_can_authenticate_user(self):
        """
        A third-party website for a domain must be able to obtain an AuthToken for its users.
        """
        current_ip = facade.models.AuthToken.objects.all()[0].ip

        # create domain
        ret = self.domain_manager.create(self.admin_token, 'Remote Domain 1', {'authentication_ip' : current_ip})
        self.assertEquals(ret['status'], 'OK')
        domain_id = ret['value']['id']

        ret = self.domain_manager.change_password(self.admin_token, domain_id, 'new password')
        self.assertEquals(ret['status'], 'OK')

        student_id, student_at = self.create_student()

        # get the domain PK as the newly created user
        ret = self.domain_manager.get_filtered(student_at, {'exact' : {'name' : 'Remote Domain 1'}}, ['id'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        domain_id = ret['value'][0]['id']

        # Student can self-affiliate with the domain
        ret = self.domain_affiliation_manager.create(student_at, student_id, domain_id, 'user456', {'may_log_me_in' : True})
        self.assertEquals(ret['status'], 'OK')

        ret = self.user_manager.obtain_auth_token_voucher('Remote Domain 1', 'user456', 'new password')
        self.assertEquals(ret['status'], 'OK')
        atv = ret['value']

        ret = self.user_manager.redeem_auth_token_voucher(atv)
        self.assertEquals(ret['status'], 'OK')
        at = ret['value']['auth_token']

        # make sure the AuthToken works
        ret = self.user_manager.get_authenticated_user(at)
        self.assertEquals(ret['status'], 'OK')

        # make sure we fail to get an AuthTokenVoucher when using the wrong password
        ret = self.user_manager.obtain_auth_token_voucher('Remote Domain 1', 'user456', 'wrong password')
        self.assertEquals(ret['status'], 'error')

        # make sure we fail to get an AuthTokenVoucher when tried from the wrong IP address.
        ret = self.domain_manager.update(self.admin_token, domain_id, {'authentication_ip' : '1.2.3.4'})
        self.assertEquals(ret['status'], 'OK')

        ret = self.user_manager.obtain_auth_token_voucher('Remote Domain 1', 'user456', 'new password')
        self.assertEquals(ret['status'], 'error')

    def test_admin_can_change_user_password(self):
        user_id = self.user_manager.create(self.admin_token, 'ringo', 'password1', 'Mr.', 'Ringo', 'Starr', '124.235.3456', 'ringo@starr.com',
            'active')['value']['id']
        ret = self.user_manager.change_password(self.admin_token, user_id, 'password2')
        self.assertEquals(ret['status'], 'OK')
        ret = self.user_manager.login('ringo', 'password1')
        self.assertEquals(ret['status'], 'error')
        self.assertEquals(ret['error'][0], 17)
        ret = self.user_manager.login('ringo', 'password2')
        self.assertEquals(ret['status'], 'OK')

    def test_admin_read_and_update(self):
        user_id = self.user_manager.create(self.admin_token, 'flockOfSeagulls', 'password', 'Mr.', 'Flock o\'', 'Seagulls', '911',
            'flockofseagulls@americanri.com', 'active')['value']['id']
        res = self.user_manager.update(self.admin_token, user_id, {'first_name' : 'Flock of'})
        self.assertEquals(res['status'], 'OK')
        res = self.user_manager.get_filtered(self.admin_token, {'exact' : {'id' : user_id}}, ['first_name'])
        self.assertEquals(res['status'], 'OK')
        self.assertEquals(res['value'][0]['first_name'], 'Flock of')

    def test_logout(self):
        ret = self.user_manager.logout(self.admin_token)
        self.assertEquals(ret['status'], 'OK')

    def test_login(self):
        inactive_user_id = self.user_manager.create(self.admin_token, 'inactive_user', 'password', 'Ms.', 'Inactive', 'User', '911',
            'inactive@user.com', 'active')['value']['id']
        
        res = self.user_manager.login('inactive_user', 'password')
        self.assertEquals(res['status'], 'OK')
        self.assertTrue('expiration' in res['value'])

        # make sure sending a password with a non-ASCII character for authentication
        # doesn't choke the system
        right_now = datetime.utcnow()
        ret = self.user_manager.login(u'inactive_user', u'passwörd')
        self.assertEquals(ret['status'], 'error')
        self.assertEquals(ret['error'][0], 17) # authentication failure exception
        self.assertTrue(datetime.utcnow() - right_now > timedelta(seconds = settings.AUTHENTICATION_FAILURE_DELAY))

        res = self.user_manager.update(self.admin_token, inactive_user_id, {'status' : 'inactive'})
        res = self.user_manager.login('inactive_user', 'password')
        self.assertEquals(res['status'], 'error')
        self.assertEquals(res['error'][0], 107) # Inactive user exception
        
        # Test what happens for a suspended user
        res = self.user_manager.update(self.admin_token, inactive_user_id, {'status' : 'suspended'})
        res = self.user_manager.login('inactive_user', 'password')
        self.assertEquals(res['status'], 'error')
        self.assertEquals(res['error'][0], 114) # suspended user exception

    def test_create(self):
        res = self.user_manager.create(self.admin_token, 'biouser', 'biopassword', 'Mr.', 'Bio', 'User', '0101-10101-101', 'biouser@c.com', 'active',
            {'biography' : 'This is my bio!'})
        self.assertEquals(res['status'], 'OK')
        bio_token = self.user_manager.login('biouser', 'biopassword')['value']['auth_token']
        res = self.user_manager.get_filtered(bio_token, {'exact' : {'id' : res['value']['id']}}, ['biography'])['value'][0]
        self.assertEquals(res['biography'], 'This is my bio!')

    ## Test the creation of a blank username
    def test_create_invalid_username(self):
        # Try to create a blank username
        res = self.user_manager.create(self.admin_token, '', 'password', 'Mr.', 'Blank', 'Username', '000.000.0000', 'blank@username.com', 'active')
        self.assertEquals(res['status'], 'error')
        self.assertEquals(res['error'][0], 121) # Validation error
        # Try to create duplicate usernames
        res = self.user_manager.create(self.admin_token, 'rpbarlow', 'password', 'Mr.',
            'Randy', 'Barlow', '', '', 'active')
        self.assertEquals(res['status'], 'OK')
        res = self.user_manager.create(self.admin_token, 'rpbarlow', 'password', 'Mr.',
            'Randy', 'Barlow', '', '', 'active')
        # res should have a key 'error' because we created a duplicate user
        self.assertTrue('error' in res)
        # Try to create a username with whitespace in the name (which is now allowed!)
        res = self.user_manager.create(self.admin_token, 'r pbarlow', 'password', 'Mr.', 'Space', 'Cadet', '123.456.7890', 'space@cadet.com', 'active')
        self.assertEquals(res['status'], 'OK')
        # If a user puts a tab character in the username, they ought to be
        # hit on the head.  It's far easier to allow it than not at this point.
        res = self.user_manager.create(self.admin_token, 'r\tpbarlow', 'password', 'Mr.', 'Space', 'Cadet', '123.456.7890', 'space@cadet.com', 'active')
        self.assertEquals(res['status'], 'OK')
        # Try to create a username with an otherwise illegal character in the name
        res = self.user_manager.create(self.admin_token, 'r"pbarlow', 'password', 'Mr.', 'Space', 'Cadet', '123.456.7890', 'space@cadet.com', 'active')
        self.assertEquals(res['status'], 'error')
        self.assertEquals(res['error'][0], 121) # Validation error
        # A user in a different domain, like LDAP, shouldn't be subjected to these checks
        res = self.user_manager.create(self.admin_token, 'uspace in name', 'test', '', '', '', '', '', 'active', {'domain' : 'LDAP'})
        self.assertEquals(res['status'], 'OK')

    def test_instructor_can_read_student(self):
        instructor_id, instructor_at = self.create_instructor()
        student1_id, student1_at = self.create_student('iWillCheatOnTests', 'Mr.', 'Brett', 'Bretterson')
        student2_id, student2_at = self.create_student('iAmHonestAbe', 'Mr.', 'Abe', 'Lincoln')
        region1 = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(region1['status'], 'OK')
        venue1 = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1['value']['id'])
        self.assertEquals(venue1['status'], 'OK')
        a_product_line_id = self.product_line_manager.create(self.admin_token, 'We Win!')['value']['id']
        boring_session_template_id = self.session_template_manager.create(self.admin_token, 'boringAsItGets', 'Boring As It Gets!', '1',
            'The purpose of this session_template is for the instructor to gain experience in the important task of boring the snott out of students',
            5555555, 9, True)['value']['id']
        ret = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1', 'Description 1', self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), self.organization1, a_product_line_id, {'venue' : venue1['value']['id']})
        self.assertEquals(ret['status'], 'OK')
        event1 = ret['value']['id']
        ret = self.session_manager.create(self.admin_token, self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(),
            'active', True, 23456, event1, {'session_template' : boring_session_template_id})
        self.assertEquals(ret['status'], 'OK')
        boring_session_id = ret['value']['id']
        instructor_role_id = self.session_user_role_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Instructor'}})['value'][0]['id']
        student_role_id = self.session_user_role_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Student'}})['value'][0]['id']
        instructor_session_user_role_req_id = self.session_user_role_requirement_manager.create(self.admin_token, boring_session_id,
            instructor_role_id, 1, 1, False)['value']['id']
        student_session_user_role_req_id = self.session_user_role_requirement_manager.create(self.admin_token, boring_session_id, student_role_id, 1,
            1, False)['value']['id']
        ret = self.assignment_manager.create(self.admin_token, instructor_session_user_role_req_id, instructor_id)
        self.assertEquals(ret['status'], 'OK')
        ret = self.assignment_manager.bulk_create(self.admin_token, student_session_user_role_req_id, [student1_id, student2_id], {})
        self.assertEquals(ret['status'], 'OK')
        # The instructor should be able to see some things about the students, like email addresses
        student_query = self.user_manager.get_filtered(instructor_at, {'exact' : {'id' : student1_id}}, ['email', 'last_name'])['value']
        self.assertTrue('email' in student_query[0])
        self.assertEquals(student_query[0]['last_name'], 'Bretterson')
        # The instructor should not be able to see things about users who are not their students
        non_student_id = self.user_manager.create(self.admin_token, 'imSkippingClass', 'hooky', 'Mr.', 'Tough', 'Guy', '111.111.1111', 'tough@guy.com', 'active')['value']['id']
        non_student_query = self.user_manager.get_filtered(instructor_at, {'exact' : {'id' : non_student_id}})['value']
        self.assertTrue('first_name' not in non_student_query[0])

    def test_instructor_manager_can_read_and_update_instructors(self):
        region1 = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(region1['status'], 'OK')
        venue1 = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789', region1['value']['id'])
        self.assertEquals(venue1['status'], 'OK')

        im_id = self.user_manager.create(self.admin_token, 'im', 'impw', 'Dr.', 'Instructor', 'Manager', '111-111-1111', 'instructor@manager.com', 'active')['value']['id']
        i_id = self.user_manager.create(self.admin_token, 'instructor', 'ipw', 'Prof.', 'Instructor', 'Instructor', '222-222-2222', 'instructor@instructor.com',
            'active')['value']['id']
        s_id = self.user_manager.create(self.admin_token, 'student', 'spw', 'Mr.', 'Learning', 'Professional', '333.333.3333', 'student@student.edu',
            'active')['value']['id']
        r_id = self.user_manager.create(self.admin_token, 'regularUser', 'rpw', 'Ms.', 'Regular', 'User', '444.444.4444', 'regular@user.net',
            'active')['value']['id']
        product_line_id = self.product_line_manager.create(self.admin_token, 'Product Line')['value']['id']
        session_template_id = self.session_template_manager.create(self.admin_token, 'testCourse', 'Test Course', '1', 'A Test Course', 234, 9,
            True)['value']['id']
        self.session_template_manager.update(self.admin_token, session_template_id, {'product_line' : product_line_id})
        event1 = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1', 'Description 1', self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), self.organization1, product_line_id, {'venue' : venue1['value']['id']})['value']['id']
        session_id = self.session_manager.create(self.admin_token, self.right_now.isoformat(), (self.right_now+self.one_day).isoformat(), 'active',
            True, 23456, event1, {'session_template' : session_template_id})['value']['id']
        instructor_role_id = self.session_user_role_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Instructor'}})['value'][0]['id']
        student_role_id = self.session_user_role_manager.get_filtered(self.admin_token, {'exact' : {'name' : 'Student'}})['value'][0]['id']
        instructor_session_user_role_req_id = self.session_user_role_requirement_manager.create(self.admin_token, session_id, instructor_role_id, 1,
            1, False)['value']['id']
        student_session_user_role_req_id = self.session_user_role_requirement_manager.create(self.admin_token, session_id, student_role_id, 1,
            1, False)['value']['id']
        res = self.session_user_role_requirement_manager.update(self.admin_token, instructor_session_user_role_req_id, {'users' : [i_id]})
        self.assertEquals(res['status'], 'OK')
        res = self.session_user_role_requirement_manager.update(self.admin_token, student_session_user_role_req_id, {'users' : [s_id]})
        self.assertEquals(res['status'], 'OK')
        # Add the instructor manager and the instructor to the product line
        res = self.product_line_manager.update(self.admin_token, product_line_id, {'instructor_managers' : [im_id]})
        self.assertEquals(res['status'], 'OK')
        res = self.product_line_manager.update(self.admin_token, product_line_id, {'instructors' : [i_id]})
        self.assertEquals(res['status'], 'OK')
        # The instructor manager should be able to change the instructor's first name
        im_auth_token = self.user_manager.login('im', 'impw')['value']['auth_token']
        res = self.user_manager.update(im_auth_token, i_id, {'first_name' : 'Course'})
        self.assertEquals(res['status'], 'OK')
        res = self.user_manager.get_filtered(im_auth_token, {'exact' : {'id' : i_id}}, ['first_name', 'phone'])
        self.assertEquals(res['status'], 'OK')
        self.assertEquals(res['value'][0]['first_name'], 'Course')
        # The instructor manager should be able to see a lot of information about the instructor, like phone number
        self.assertEquals(res['value'][0]['phone'], '222-222-2222')
        # The instructor manager should not be able to see anything special about a student
        res = self.user_manager.get_filtered(im_auth_token, {'exact' : {'id' : s_id}})
        self.assertTrue('phone' not in res['value'][0])
        # The instructor manager should not be able to see anything special about an unrelated user
        res = self.user_manager.get_filtered(im_auth_token, {'exact' : {'id' : r_id}})
        self.assertTrue('phone' not in res['value'][0])

    def test_modify_self(self):
        user1_id = self.user_manager.create(self.admin_token, 'around', 'you', 'Mr.', 'Lost', 'Enough', '704-123-4567',
            'lost@enough.com', 'active')['value']['id']
        user2_id = self.user_manager.create(self.admin_token, 'website', 'man', 'Mr.', 'Website', 'Man', '919-123-4567',
            'website@man.com', 'active')['value']['id']
        auth_token1 = self.user_manager.login('around', 'you')['value']['auth_token']
        auth_token2 = self.user_manager.login('website', 'man')['value']['auth_token']
        res = self.user_manager.change_password(auth_token1, user1_id, 'me', 'you')
        self.assertEquals(res['status'], 'OK')
        res = self.user_manager.change_password(auth_token1, user2_id, 'woman')
        self.assertEquals(res['status'], 'error')
        self.assertEquals(res['error'][0], 23)
        res = self.user_manager.update(auth_token1, user1_id, {'title' : 'Ms.'})
        self.assertEquals(res['status'], 'OK')
        res = self.user_manager.get_filtered(auth_token1, {'exact' : {'id' : user1_id}}, ['title'])
        self.assertEquals(res['status'], 'OK')
        self.assertEquals(res['value'][0]['title'], 'Ms.')
        res = self.user_manager.change_password(self.admin_token, user2_id, 'woman')
        self.assertEquals(res['status'], 'OK')

    def test_modify_someone_else_without_permissions(self):
        user1_id = self.user_manager.create(self.admin_token, 'around', 'you', 'Mr.', 'Lost', 'Enough', '704-123-4567',
            'lost@enough.com', 'active')['value']['id']
        user2_id = self.user_manager.create(self.admin_token, 'website', 'man', 'Mr.', 'Website', 'Man', '919-123-4567',
            'website@man.com', 'active')['value']['id']
        auth_token1 = self.user_manager.login('around', 'you')['value']['auth_token']
        auth_token2 = self.user_manager.login('website', 'man')['value']['auth_token']
        res = self.user_manager.update(auth_token1, user2_id, {'first_name' : 'Secret Agent'})
        self.assertEquals(res['status'], 'error')
        self.assertEquals(res['error'][0], 23)
        res = self.user_manager.get_filtered(auth_token2, {'exact' : {'id' : user2_id}}, ['first_name'])
        self.assertEquals(res['value'][0]['first_name'], 'Website')

    def test_product_line_manager_access_instructor(self):
        # create a region
        ret = self.region_manager.create(self.admin_token, 'Region 1')
        self.assertEquals(ret['status'], 'OK')
        region_1_id = ret['value']['id']
        # create a venue in that region
        ret = self.venue_manager.create(self.admin_token, 'Venue 1', '123456789',
            region_1_id)
        self.assertEquals(ret['status'], 'OK')
        venue_1_id = ret['value']['id']

        # create a product line manager user
        ret = self.user_manager.create(self.admin_token, 'plm', 'plmpw', 'Dr.', 'Product Line',
            'Manager', '111-111-1111', 'productLine@manager.com', 'active')
        self.assertEquals(ret['status'], 'OK')
        plm_id = ret['value']['id']
        
        # create an instructor user
        ret = self.user_manager.create(self.admin_token, 'instructor', 'ipw', 'Prof.', 'Instructor',
            'Instructor', '222-222-2222', 'instructor@instructor.com',
            'active')
        self.assertEquals(ret['status'], 'OK')
        instructor_id = ret['value']['id']
        
        # create a student user
        ret = self.user_manager.create(self.admin_token, 'student', 'spw', 'Mr.', 'Learning', 'Professional', '333.333.3333', 'student@student.edu',
            'active')
        self.assertEquals(ret['status'], 'OK')
        student_id = ret['value']['id']
        
        # now create a regular user
        ret = self.user_manager.create(self.admin_token, 'regularUser', 'rpw', 'Ms.', 'Regular', 'User', '444.444.4444', 'regular@user.net',
            'active')
        self.assertEquals(ret['status'], 'OK')
        regular_user_id = ret['value']['id']
        
        # create a product line
        ret = self.product_line_manager.create(self.admin_token, 'Product Line')
        self.assertEquals(ret['status'], 'OK')
        product_line_id = ret['value']['id']
        
        # now create a session template
        ret = self.session_template_manager.create(self.admin_token, 'testCourse', 'Test Course', '1', 'A Test Course', 234,
            9, True)
        self.assertEquals(ret['status'], 'OK')
        session_template_id = ret['value']['id']
            
        # now make the session template part of the product line created previously
        ret = self.session_template_manager.update(self.admin_token, session_template_id, {'product_line' : product_line_id})
        self.assertEquals(ret['status'], 'OK')
        
        # now create an event, and a session within it based on the previously created session template
        event_start_time = self.right_now.isoformat()
        event_end_time = (self.right_now + self.one_day).isoformat()
        ret = self.event_manager.create(self.admin_token, 'Name 1', 'Title 1', 'Description 1', event_start_time,
            event_end_time, self.organization1, product_line_id, {'venue' : venue_1_id})
        self.assertEquals(ret['status'], 'OK')
        event_1_id = ret['value']['id']
        # create the session to go into the event 
        ret = self.session_manager.create(self.admin_token, event_start_time, event_end_time,'active',
            True, 23456, event_1_id, {'session_template' : session_template_id})
        self.assertEquals(ret['status'], 'OK')
        session_id = ret['value']['id']
            
        # retrieve the student and instructor session user roles
        ret = self.session_user_role_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'Instructor'}})
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        instructor_role_id = ret['value'][0]['id']
        ret = self.session_user_role_manager.get_filtered(self.admin_token,
            {'exact' : {'name' : 'Student'}})
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        student_role_id = ret['value'][0]['id']
        
        # create the relevant session user role requirements
        ret = self.session_user_role_requirement_manager.create(
            self.admin_token, session_id, instructor_role_id, 1, 1, False)
        self.assertEquals(ret['status'], 'OK')
        instructor_surr_id = ret['value']['id']
        ret = self.session_user_role_requirement_manager.create(
            self.admin_token, session_id, student_role_id, 1, 1, False)
        self.assertEquals(ret['status'], 'OK')
        student_surr_id = ret['value']['id']
        
        # "enroll" the instructor
        ret = self.assignment_manager.create(self.admin_token, instructor_surr_id, instructor_id)
        self.assertEquals(ret['status'], 'OK')
        
        # enroll the student
        ret = self.assignment_manager.create(self.admin_token, student_surr_id, student_id)
        self.assertEquals(ret['status'], 'OK')
        
        # Add the product line manager and the instructor manager to the product line
        ret = self.product_line_manager.update(self.admin_token, product_line_id, {'managers' : [plm_id]})
        self.assertEquals(ret['status'], 'OK')
        ret = self.product_line_manager.update(self.admin_token, product_line_id, {'instructors' : [instructor_id]})
        self.assertEquals(ret['status'], 'OK')
        
        # The product line manager should be able to change the instructor's last name
        ret = self.user_manager.login('plm', 'plmpw')
        self.assertEquals(ret['status'], 'OK')
        plm_auth_token = ret['value']['auth_token']
        ret = self.user_manager.update(plm_auth_token, instructor_id, {'last_name' : 'Man'})
        self.assertEquals(ret['status'], 'OK')
        
        ret = self.user_manager.get_filtered(plm_auth_token, {'exact' : {'id' : instructor_id}}, ['last_name', 'phone'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        instructor_user_data = ret['value'][0]
        self.assertEquals(instructor_user_data['last_name'], 'Man')
        # The product line manager should be able to see a lot of information about the instructor, like phone number
        self.assertEquals(instructor_user_data['phone'], '222-222-2222')
        
        # The product line manager should not be able to see anything special about a student
        ret = self.user_manager.get_filtered(plm_auth_token, {'exact' : {'id' : student_id}})
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        student_user_data = ret['value'][0]
        self.assertTrue('phone' not in student_user_data)
        
        # The product line manager should not be able to see anything special about an unrelated user
        ret = self.user_manager.get_filtered(plm_auth_token, {'exact' : {'id' : regular_user_id}})
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        regular_user_data = ret['value'][0]
        self.assertTrue('phone' not in regular_user_data)

    def test_prd_line_mgrs_updte_instrctr_crdntls(self):
        plm_id = self.user_manager.create(self.admin_token, 'productLineManagerMan', 'plmpw', 'Dr.', 'Product Line', 'Manager', '111-111-1111',
            'productLine@manager.com', 'active')['value']['id']
        plm_auth_token = self.user_manager.login('productLineManagerMan', 'plmpw')['value']['auth_token']
        i_id = self.user_manager.create(self.admin_token, 'instructor', 'ipw', 'Prof.', 'Instructor', 'Instructor', '222-222-2222',
            'instructor@instructor.com', 'active')['value']['id']
        product_line_id = self.product_line_manager.create(self.admin_token, 'Product Line')['value']['id']
        # Add the product line manager to the product line
        res = self.product_line_manager.update(self.admin_token, product_line_id, {'managers' : [plm_id]})
        res = self.product_line_manager.get_filtered(self.admin_token, {})
        self.assertEquals(res['status'], 'OK')
        # Add the instructor to the product line
        res = self.product_line_manager.update(plm_auth_token, product_line_id, {'instructors' : [i_id]})
        self.assertEquals(res['status'], 'OK')
        # Create some credentials, and give them to the instructor
        phd_id = self.credential_type_manager.create(self.admin_token, 'Ph.D.', 'Philosophical Doctorate')['value']['id']
        phd_physics_id = self.credential_manager.create(self.admin_token, i_id, phd_id)['value']['id']
        # See if the product line manager can read the instructor's credentials
        res = self.user_manager.get_filtered(plm_auth_token, {'exact' : {'id' : i_id}}, ['credentials'])
        self.assertEquals(res['value'][0]['credentials'][0], int(phd_physics_id))

    def test_read_someone_else_without_permission(self):
        user1_id = self.user_manager.create(self.admin_token, 'around', 'you', 'Mr.', 'Lost', 'Enough', '704-123-4567',
            'lost@enough.com', 'active')['value']['id']
        user2_id = self.user_manager.create(self.admin_token, 'website', 'man', 'Mr.', 'Website', 'Man', '919-123-4567',
            'website@man.com', 'active')['value']['id']
        auth_token1 = self.user_manager.login('around', 'you')['value']['auth_token']
        res = self.user_manager.get_filtered(auth_token1, {'exact' : {'id' : user2_id}}, ['last_name'])
        self.assertEquals(res['status'], 'OK')
        self.assertEquals(len(res['value']), 1)
        self.assertTrue('last_name' not in res['value'][0])
        self.assertTrue('phone' not in res['value'][0])
        
    def test_renew_authentication(self):
        reauth_user = self.user_manager.create(self.admin_token, 'reauth_user', 'reauth_password', 'Ms.', 'Needs To', 'Reauthenticate',
            '123-456-7890', 'helpme@reauthenticate.com', 'active')
        auth_token1 = self.user_manager.login('reauth_user', 'reauth_password')
        auth_token2 = self.user_manager.relogin(auth_token1['value']['auth_token'])
        self.assertEquals(auth_token2['status'], 'OK')
        ret = self.user_manager.get_authenticated_user(auth_token2['value']['auth_token'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value']['username'], 'reauth_user')
        self.assertEquals(ret['value']['domain'], 'local')

    def test_reset_password(self):
        forgetful_user = self.user_manager.create(self.admin_token, 'iWillForget', 'This', 'Mr.', 'Password', 'This', '913-495-6943', 'forgetful@user.com',
            'active', {'email2' : 'correct@email.com'})
        auth_token = self.user_manager.login('iWillForget', 'This')
        self.assertEquals(auth_token['status'], 'OK')
        # Wrong e-mail address
        pw_reset = self.user_manager.reset_password('iWillForget', 'forgetful1@user.com')
        # This should raise an object not found error
        self.assertEquals(pw_reset['error'][0], 97)
        # Right e-mail address (primary email address)
        pw_reset = self.user_manager.reset_password('iWillForget', 'forgetful@user.com')
        self.assertEquals(pw_reset['status'], 'OK')
        # Right e-mail address (second email address)
        pw_reset = self.user_manager.reset_password('iWillForget', 'correct@email.com')
        self.assertEquals(pw_reset['status'], 'OK')

    def test_addresses(self):
        the_dude_id = self.user_manager.create(self.admin_token, 'theDude', 'anotherCaucasianGary', 'Mr.', 'Jeff "The Dude"', 'Lebowski', '601-123-4567',
            'obviouslyYoureNotAGolfer@whatsThisBowlingBall.com', 'active')['value']['id']
        the_dudes_auth_token = self.user_manager.login('theDude', 'anotherCaucasianGary')['value']['auth_token']
        ret = self.user_manager.update(the_dudes_auth_token, the_dude_id, {'shipping_address' : {'country' : 'US', 'label' : 'myaddr1\nmyaddr2', 'region' : 'NC',
            'locality' : 'Raleigh', 'postal_code' : '12345'}})
        self.assertEquals(ret['status'], 'OK')
        ret = self.user_manager.get_filtered(the_dudes_auth_token, {'exact' : {'id' : the_dude_id}}, ['shipping_address', 'billing_address'])
        self.assertEquals(ret['value'][0]['shipping_address']['label'], 'myaddr1\nmyaddr2')
        ret = self.user_manager.update(the_dudes_auth_token, the_dude_id, {'shipping_address' : {'country' : 'US', 'label' : '170 Southport Drive',
            'region' : 'NC', 'locality' : 'Morrisville', 'postal_code' : '27560'}, 'billing_address' : {'country' : 'US', 'label' : 'myaddr1\nmyaddr2',
            'region' : 'NC', 'locality' : 'Raleigh', 'postal_code' : '12345'}})
        self.assertEquals(ret['status'], 'OK')
        ret = self.user_manager.get_filtered(the_dudes_auth_token, {'exact' : {'id' : the_dude_id}}, ['shipping_address', 'billing_address'])
        self.assertEquals(ret['value'][0]['shipping_address']['label'], '170 Southport Drive')
        self.assertEquals(ret['value'][0]['billing_address']['label'], 'myaddr1\nmyaddr2')

    def test_generate_username(self):
        ret = self.user_manager.generate_username('', ' Johannes', '  O\'Bryant ')
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(ret['value'], 'jobryant')
        ret = self.user_manager.create(self.admin_token, ret['value'], 'password', 'Mr.', ' Johannes', '  O\'Bryant ', '919-228-4971', 'j@b.com', 'active')
        self.assertEquals(ret['status'], 'OK')

    def test_suggest_username_like(self):
        ret = self.user_manager.suggest_username_like('', ' r!%p$b&a r^^=l()o][w?{}')
        self.assertEquals(ret['status'], 'OK')
        # rpbarlow should be an OK suggestion for the system, since no user has been created by that name yet
        self.assertEquals(ret['value'], 'rpbarlow')
        ret = self.user_manager.create(self.admin_token, ret['value'], 'password', 'Mr.', 'Randy', 'Barlow', '919-228-4971', 'rbarlow@americanri.com', 'active')
        self.assertEquals(ret['status'], 'OK')
        ret = self.user_manager.suggest_username_like('', ' r!%p$b&a r^^=l()o][w?{}')
        self.assertEquals(ret['status'], 'OK')
        # rpbarlow should generate rpbarlow0 now
        self.assertEquals(ret['value'], 'rpbarlow1')
        ret = self.user_manager.create(self.admin_token, ret['value'], 'password', 'Mr.', 'Randy', 'Barlow, II', '919-228-4971', 'rbarlow2@americanri.com', 'active')
        self.assertEquals(ret['status'], 'OK')
        ret = self.user_manager.suggest_username_like('', ' r!%p$b&a r^^=l()o][w?{}')
        self.assertEquals(ret['status'], 'OK')
        # rpbarlow should generate rpbarlow1 now
        self.assertEquals(ret['value'], 'rpbarlow2')
        ret = self.user_manager.create(self.admin_token, ret['value'], 'password', 'Mr.', 'Randy', 'Barlow, III', '919-228-4971', 'rbarlow3@americanri.com', 'active')
        self.assertEquals(ret['status'], 'OK')

    def test_preferred_venues(self):
        ret = self.user_manager.create(self.admin_token, 'picky_user', 'password', 'Ms.', 'Picky', 'User', '919-919-1919', 'picky@user.edu', 'active')
        picky_user_id = ret['value']['id']
        home_id = self.region_manager.create(self.admin_token, 'Home')['value']['id']
        close_to_home_id = self.venue_manager.create(self.admin_token, 'Close To Home', '911', home_id)['value']['id']
        picky_at = self.user_manager.login('picky_user', 'password')['value']['auth_token']
        res = self.user_manager.get_filtered(picky_at, {'exact' : {'id' : picky_user_id}}, ['preferred_venues'])
        self.assertEquals(res['status'], 'OK')
        self.assertEquals(len(res['value'][0]['preferred_venues']), 0)
        res = self.user_manager.update(picky_at, picky_user_id, {'preferred_venues' : [close_to_home_id]})
        self.assertEquals(res['status'], 'OK')
        res = self.user_manager.get_filtered(picky_at, {'exact' : {'id' : picky_user_id}}, ['preferred_venues'])
        self.assertEquals(res['status'], 'OK')
        self.assertEquals(res['value'][0]['preferred_venues'][0], int(close_to_home_id))
        
    def test_get_filtered_case_insensitive(self):
        res = self.user_manager.create(self.admin_token, 'obamaMania', 'password', 'Mr.',
            'Obama', 'Mania', '', '', 'active')
        ret = self.user_manager.get_filtered(self.admin_token,
            {'iexact': {'last_name' : 'maNIa'}}, ['id', 'first_name'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        self.assertEquals(ret['value'][0]['first_name'], 'Obama')
        ret = self.user_manager.get_filtered(self.admin_token,
            {'icontains': {'last_name' : 'ANiA'}}, ['id', 'first_name'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        self.assertEquals(ret['value'][0]['first_name'], 'Obama')
        ret = self.user_manager.get_filtered(self.admin_token,
            {'ibegins': {'last_name' : 'mAnI'}}, ['id', 'first_name'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        self.assertEquals(ret['value'][0]['first_name'], 'Obama')
        ret = self.user_manager.get_filtered(self.admin_token,
            {'iends': {'last_name' : 'AnIA'}}, ['id', 'first_name'])
        self.assertEquals(ret['status'], 'OK')
        self.assertEquals(len(ret['value']), 1)
        self.assertEquals(ret['value'][0]['first_name'], 'Obama')

    def test_single_use_auth_token(self):
        student_id, student_at = self.create_student()
        product_line1 = self.product_line_manager.create(self.admin_token,
            'Product Line 1')['value']['id']
        # test success
        suat = self.user_manager.obtain_single_use_auth_token(student_at)['value']
        result = self.user_manager.get_authenticated_user(suat)['value']
        self.assertEqual(result['id'], student_id)
        result = self.user_manager.get_authenticated_user(suat)
        self.assertEqual(result['error'][0], 49) # AuthTokenExpiredException
        # try to do something forbidden
        suat = self.user_manager.obtain_single_use_auth_token(student_at)['value']
        result = self.group_manager.create(suat, 'agroup')
        self.assertEqual(result['error'][0], 23) # PermissionDeniedException
        result = self.user_manager.get_authenticated_user(suat)
        self.assertEqual(result['error'][0], 49) # AuthTokenExpiredException
        # try to do something that fails model validation
        # need to be admin since only admin can create relevant models
        suat = self.user_manager.obtain_single_use_auth_token(self.admin_token)['value']
        result = self.event_manager.create(suat, 'Event1', 'Event1', 'Event1',
            '1994-11-06', '1994-11-05', self.organization1, product_line1)
        self.assertEqual(result['error'][0], 121) # ValidationException
        result = self.user_manager.get_authenticated_user(suat)
        self.assertEqual(result['error'][0], 49) # AuthTokenExpiredException
        # let's make sure you can't extend the validity of a single-use token
        suat = self.user_manager.obtain_single_use_auth_token(student_at)['value']
        result = self.user_manager.relogin(suat)
        self.assertEqual(result['error'][0], 17) # AuthenticationFailureException
        result = self.user_manager.get_authenticated_user(suat)
        self.assertEqual(result['error'][0], 49) # AuthTokenExpiredException
        # let's make sure you can't obtain a single use token using another
        # single use token
        suat = self.user_manager.obtain_single_use_auth_token(student_at)['value']
        result = self.user_manager.obtain_single_use_auth_token(suat)
        self.assertEqual(result['error'][0], 17) # AuthenticationFailureException
        result = self.user_manager.get_authenticated_user(suat)
        self.assertEqual(result['error'][0], 49) # AuthTokenExpiredException

    def test_self_registered_users_must_be_pending(self):
        for status in ['', 'active', 'inactive', 'qualified', 'suspended', 'training']:
            result = self.user_manager.create('', 'randomuser',
                'initial_password', 'Mr.', 'First', 'Last', '555.555.1212',
                'random@example.net', status)
            self.assertEqual(result['status'], 'error')
            self.assertEqual(result['error'][0], 23) # permission denied
        result = self.user_manager.create('', 'randomuser',
            'initial_password', 'Mr.', 'First', 'Last', '555.555.1212',
            'random@example.net', 'pending')
        self.assertEqual(result['status'], 'OK')

class TestLogging(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.log_manager = self.svcGateway.getService('LogManager')

    def test_log(self):
        ret = self.log_manager.critical(self.admin_token, 'this is a critical test')
        self.assertEquals(ret['status'], 'OK')
        ret = self.log_manager.error(self.admin_token, 'this is an error test')
        self.assertEquals(ret['status'], 'OK')
        ret = self.log_manager.warning(self.admin_token, 'this is a warning test')
        self.assertEquals(ret['status'], 'OK')
        ret = self.log_manager.info(self.admin_token, 'this is an info test')
        self.assertEquals(ret['status'], 'OK')
        ret = self.log_manager.debug(self.admin_token, 'this is a debug test')
        self.assertEquals(ret['status'], 'OK')
        ret = self.log_manager.error('this is not a valid auth token',
            'this is an invalid auth token test')
        self.assertEquals(ret['status'], 'error')
        self.assertEquals(ret['error'][0], 128) # NotLoggedInException
        ret = self.log_manager.error('', 'this is a guest auth token test')
        self.assertEquals(ret['status'], 'error')
        self.assertEquals(ret['error'][0], 23) # permission denied exception
        ret = self.log_manager.error(None, 'this is a guest auth token test')
        self.assertEquals(ret['status'], 'error')
        self.assertEquals(ret['error'][0], 23) # permission denied exception

class TestUtilsManager(TestCase):
    def test_get_choices(self):
        # check the invalid model name case
        ret = self.utils_manager.get_choices('not_a_model', 'aspect_ratio')
        self.assertEquals(ret['status'], 'error')
        self.assertEquals(ret['error'][0], 4) # field name not recognized
        # check the invalid field name case
        ret = self.utils_manager.get_choices('Video', 'not_a_field')
        self.assertEquals(ret['status'], 'error')
        self.assertEquals(ret['error'][0], 4) # field name not recognized
        # check that we gen an empty list for a field that has no choices
        list = self.utils_manager.get_choices('Video', 'live')['value']
        self.assertEquals(len(list), 0)
        # check a couple of fields with choices
        list = self.utils_manager.get_choices('Video', 'aspect_ratio')['value']
        self.assertEquals(len(list), 2)
        self.assertEquals(list[0], '4:3')
        self.assertEquals(list[1], '16:9')
        list = self.utils_manager.get_choices('Question', 'widget')['value']
        self.assertEquals(len(list), 25)

class TestCelerybeatTasks(TestCase):
    def disabled_test_celerybeat_tasks(self):
        # create a used single-use and an expired ordinary token
        student_id, student_at = self.create_student()
        suat = self.user_manager.obtain_single_use_auth_token(student_at)['value']
        self.user_manager.get_authenticated_user(suat)
        at = facade.models.AuthToken.objects.get(session_id = student_at)
        at.time_of_expiration = datetime.utcnow()-timedelta(days=1)
        at.save()
        # create an expired and a non-expired credential
        credential_type = facade.models.CredentialType.objects.create(
            name='B.S.', description='Electrical Engineering')
        student = facade.models.User.objects.get(id=student_id)
        cred = facade.models.Credential(user=student, owner=student,
            credential_type=credential_type)
        cred.date_expires = date.today()+timedelta(days=1)
        cred.save()
        exp_cred = facade.models.Credential(user=student, owner=student,
            credential_type=credential_type)
        exp_cred.date_expires = date.today()-timedelta(days=1)
        exp_cred.save()

        refresh_db()
        logdir = tempfile.mkdtemp()
        # we need to run both celerybeat and celeryd, since celerybeat appears
        # to ignore CELERY_ALWAYS_EAGER and always runs the task via the
        # broker...
        daemon_pid = os.fork()
        if not daemon_pid:
            os.chdir(settings.PROJECT_ROOT)
            os.execl('./manage.py', './manage.py', 'celeryd',
                '-l', 'DEBUG',
                '-f', os.path.join(logdir, 'celeryd.log'))
        beat_pid = os.fork()
        if beat_pid:
            time.sleep(3)
            os.kill(beat_pid, signal.SIGTERM)
            beat_exit_status = os.waitpid(beat_pid, 0)
        else:
            os.chdir(settings.PROJECT_ROOT)
            os.execl('./manage.py', './manage.py', 'celerybeat',
                '--settings', 'celerybeat_test_settings',
                '-l', 'DEBUG',
                '-f', os.path.join(logdir, 'celerybeat.log'),
                '-s', os.path.join(logdir, 'celerybeat.schedule'))
        time.sleep(1) # wait for tasks to finish running
        os.kill(daemon_pid, signal.SIGTERM)
        daemon_exit_status = os.waitpid(daemon_pid, 0)
        shutil.rmtree(logdir)
        self.assertEqual(daemon_exit_status[1], 0)
        self.assertEqual(beat_exit_status[1], 0)
        refresh_db()

        # check that the used single-use and expired ordinary token are gone
        self.assertEquals(facade.models.AuthToken.objects.filter(
            session_id = suat).count(), 0)
        self.assertEquals(facade.models.AuthToken.objects.filter(
            session_id = student_at).count(), 0)
        # check that the expired credential was marked expired, the other wasn't
        result = self.credential_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : cred.id}}, ['status'])['value'][0]
        self.assertEqual(result['status'], 'pending')
        result = self.credential_manager.get_filtered(self.admin_token,
            {'exact' : {'id' : exp_cred.id}}, ['status'])['value'][0]
        self.assertEqual(result['status'], 'expired')

################################################################################################################################################
#
# Below this comment block is found utility code that is used to facilitate some of the above unit tests.
#
################################################################################################################################################
def initialize_db():
    if getattr(settings, 'SVC_TEST_REMOTE', False):
        # We must use the 'flush' command instead of piping the 'sqlflush' command's
        # output to the database like we used to so that the post_syncdb hook
        # on the contenttypes app gets invoked, clearing the content type cache.
        call_command('flush', verbosity=0, interactive=False)
        call_command('setup')
    else:
        call_command('setup')
        transaction.commit()

def refresh_db():
    """
    Do whatever magic may be necessary to view database changes
    made by the backend.
    """
    transaction.enter_transaction_management()
    transaction.commit()
    transaction.leave_transaction_management()
    django.db.connection.close()
    django.db.connection = django.db.backend.DatabaseWrapper(settings.DATABASES[django.db.DEFAULT_DB_ALIAS])

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

# vim:tabstop=4 shiftwidth=4 expandtab
