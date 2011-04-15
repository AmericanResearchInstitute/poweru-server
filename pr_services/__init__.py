import uuid as _uuid
from pr_messaging import signals as _signals
from . import handlers as _handlers

# Add the dispatch_uid when connecting a signal.
_connect = lambda x, y: x.connect(y, dispatch_uid=str(_uuid.uuid4()))

# Connect handlers to messaging app signals.
_connect(_signals.participant_instance_requested, _handlers.pr_user_instance_requested)
_connect(_signals.participant_contact_requested, _handlers.pr_user_contact_requested)

# Python
import unittest

# Django
from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner, TestCase
from django.test.simple import build_suite, build_test, get_app, get_apps, reorder_suite

# Monkeypatch to skip third-party app tests, based on:
# http://code.djangoproject.com/attachment/ticket/13873/TEST_SKIP_APP_TESTS.diff
def _build_suite(self, test_labels, extra_tests=None, **kwargs):
    suite = unittest.TestSuite()
    if test_labels:
        for label in test_labels:
            if '.' in label:
                suite.addTest(build_test(label))
            else:
                app = get_app(label)
                suite.addTest(build_suite(app))
    else:
        for app in get_apps():
            app_name = app.__name__
            if app_name.endswith('.models'):
                app_name = app_name[:-7]
            if app_name not in getattr(settings, 'TEST_SKIP_APP_TESTS', ()):
                suite.addTest(build_suite(app))
    if extra_tests:
        for test in extra_tests:
            suite.addTest(test)

    return reorder_suite(suite, (TestCase,))
DjangoTestSuiteRunner.build_suite = _build_suite
