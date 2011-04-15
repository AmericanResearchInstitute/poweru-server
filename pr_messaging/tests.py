import logging
from django.test import TestCase
from django.conf import settings
from django.core import mail
from celery import conf
from .handlers import request_started, request_finished, got_request_exception
from .models import MessageFormat, MessageType, MessageTemplate, SentMessage
from .common import Immutable, Participant, Message
from . import send_message, message_admins, message_managers, enable_messages

if 'django.contrib.auth' in settings.INSTALLED_APPS:
    from django.contrib.auth.models import User
else:
    User = None

class TestCase(TestCase):
    
    def setUp(self):
        super(TestCase, self).setUp()
        # Modify the celery configuration to run tasks eagerly for unit tests.
        self._always_eager = conf.ALWAYS_EAGER
        conf.ALWAYS_EAGER = True
        
    def tearDown(self):
        conf.ALWAYS_EAGER = self._always_eager
        super(TestCase, self).tearDown()

class TestImmutables(TestCase):
    
    def test_immutable(self):
        i0 = Immutable()
        self.assertFalse(hasattr(i0, 'name'))
        self.assertRaises(TypeError, setattr, i0, 'name', 'something')
        self.assertRaises(TypeError, delattr, i0, 'name')
        i1 = Immutable(name='something')
        self.assertEqual(i1.name, 'something')
        self.assertRaises(TypeError, setattr, i1, 'name', 'something')
        self.assertRaises(TypeError, delattr, i1, 'name')
        i2 = i1.clone()
        self.assertTrue(i2 is not i1)
        self.assertEqual(i1.__dict__, i2.__dict__)
        i3 = i1.updated(name='something else')
        self.assertEqual(i1.name, 'something')
        self.assertEqual(i3.name, 'something else')
        i4 = i1.updated(description='this is really something')
        self.assertEqual(i1.name, i4.name)
        self.assertFalse(hasattr(i1, 'description'))
        self.assertEqual(i4.description, 'this is really something')
        self.assertTrue(repr(i4))

    def test_participant(self):
        p = Participant(None)
        self.assertRaises(TypeError, Participant, False)
        p = Participant('joe')
        self.assertEqual(p.username, 'joe')
        p = Participant('joe@user.com')
        self.assertEqual(p.email, 'joe@user.com')
        self.assertEqual(p.fullname, None)
        p = Participant('<joe@user.com>')
        self.assertEqual(p.email, 'joe@user.com')
        self.assertEqual(p.fullname, None)
        p = Participant('Joe User <joe@user.com>')
        self.assertEqual(p.email, 'joe@user.com')
        self.assertEqual(p.fullname, 'Joe User')
        p2 = Participant(p)
        self.assertEqual(p.email, p2.email)
        self.assertEqual(p.fullname, p2.fullname)
        if User:
            u = User.objects.create(username='joe', email='joe@user.com')
            p = Participant(u)
            self.assertEqual(p.email, u.email)
            self.assertEqual(p.username, u.username)
            p = Participant(u.email)
            self.assertEqual(p.instance, u)
            p = Participant(u.username)
            self.assertEqual(p.instance, u)
        p2 = p.updated(content_type='someapp.notamodel')
        self.assertEqual(p2.instance, None)
        p2 = p.updated(instance_pk=99999)
        self.assertEqual(p2.instance, None)

    def test_message(self):
        m = Message()
        self.assertEqual(m.message_type, None)
        self.assertEqual(m.context, {})
        #self.assertEqual(m.sender(), None)
        self.assertEqual(m.recipients(), [])
        m = Message(context={'hoo': 'hah'}, sender='sender@americanri.com', recipients=[])
        m = Message(recipient='user@americanri.com')
        m = Message(**{'to': ['user@americanri.com']})
        m = Message(cc=['user@americanri.com'])
        m = Message(bcc=['user@americanri.com'])
        m = m.updated(participants=[])
        self.assertEqual(m.sender(), None)
        m = Message(recipients=['user1@americanri.com', 'user2@americanri.com'])
        msgs = m.split_by_recipient()
        self.assertEqual(len(msgs), 2)

class TestMessaging(TestCase):

    def setUp(self):
        super(TestMessaging, self).setUp()
        mf = MessageFormat.objects.create(slug='email', name='Email')
        mf2 = MessageFormat.objects.create(slug='html-email', name='HTML Email')
        mt = MessageType.objects.create(slug='foo', name='Foo')
        mtp = MessageTemplate.objects.create(message_type=mt, message_format=mf,
            subject='Foo Message', body='This is a foo message body.\n\n{{ something }}')
        mtp2 = MessageTemplate.objects.create(message_type=mt, message_format=mf2,
            subject='Foo Message', body='<h1>Text message:<h1><p>{{ something }}</p>')

    def tearDown(self):
        super(TestMessaging, self).tearDown()

    def test_basic_send(self):
        send_message(message_type='foo', context={'something': 'This is something!'},
            sender=('Chris', 'cchurch@americanri.com'), recipients=['testing@americanri.com'])
        self.assertEqual(len(mail.outbox), 2)
        #for sm in SentMessage.objects.all():
        #    print sm, sm.participants.all()

    def test_send_to_admins(self):
        message_admins(message_type='foo', context={})
        self.assertEqual(len(mail.outbox), 2 * len(settings.ADMINS))

    def test_send_to_managers(self):
        message_managers(message_type='foo', context={})
        self.assertEqual(len(mail.outbox), 2 * len(settings.MANAGERS))

    def test_send_with_request(self):
        request_started(None) # Fake it for the test case.
        enable_messages(all=True)
        send_message(message_type='foo', context={}, recipients=['user@americanri.com'])
        self.assertEqual(len(mail.outbox), 0) 
        request_finished(None) # Fake it for the test case.
        self.assertEqual(len(mail.outbox), 2)

    def test_send_with_request_exception(self):
        request_started(None) # Fake it for the test case.
        send_message(message_type='foo', context={}, recipients=['user@americanri.com'])
        self.assertEqual(len(mail.outbox), 0) 
        got_request_exception(None) # Fake it for the test case.
        self.assertEqual(len(mail.outbox), 0)

class TestLogger(TestCase):

    def setUp(self):
        super(TestLogger, self).setUp()
        mf = MessageFormat.objects.create(slug='email', name='Email')
        mt = MessageType.objects.create(slug='log-message', name='Log Message')
        mtp = MessageTemplate.objects.create(message_type=mt, message_format=mf,
            subject='Log Message', body='{{ message }}')

    def tearDown(self):
        super(TestLogger, self).tearDown()

    def test_log_handler(self):
        logger = logging.getLogger('pr_messaging.tests')
        logger.error('this is a test error')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Log Message')
