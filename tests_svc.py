#!/usr/bin/env python
# RPC Client Test Suite
# 
# These tests have been moved into pr_svc_tests.tests_svc.py, but can still be
# run from this script when necessary to test against a remote server.

import unittest

# Configure Django settings.
import django.core.management
settings_module = __import__('settings')
django.core.management.setup_environ(settings_module)
from django.conf import settings

# Configure test settings from tests_svc_settings.py
settings.SVC_TEST_REMOTE = True
import tests_svc_settings
for attr in dir(tests_svc_settings):
    if attr == attr.upper():
        setattr(settings, attr, getattr(tests_svc_settings, attr))

# Import RPC tests from pr_svc_tests app.
from pr_svc_tests.tests_svc import *

if __name__=='__main__':
    unittest.main()

# vim:tabstop=4 shiftwidth=4 expandtab
