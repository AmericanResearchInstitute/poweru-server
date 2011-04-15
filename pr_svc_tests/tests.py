# Python
import os
import random
import socket
import threading
import urllib

# Django
from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers import basehttp
from django.test import TransactionTestCase
from django.test.simple import DjangoTestSuiteRunner
import django.db
from django.db import transaction, connections

# Celery
from celery import conf

# Based on: http://blog.disqus.net/2008/07/21/testing-django-applications/

# Monkey patch test runner to make it work with SQLite (by creating a database
# file instead of using an in-memory database).
_original_setup_databases = DjangoTestSuiteRunner.setup_databases
def setup_databases(self, **kwargs):
    for alias in connections:
        connection = connections[alias]
        if not connection.settings_dict['TEST_MIRROR'] and \
            connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3' and \
            connection.settings_dict['TEST_NAME'] is None:
            db_name = connection.settings_dict['NAME']
            connection.settings_dict['TEST_NAME'] = os.path.join(os.path.dirname(db_name),
                'test_' + os.path.basename(db_name))
    return _original_setup_databases(self, **kwargs)
DjangoTestSuiteRunner.setup_databases = setup_databases

class StoppableWSGIServer(basehttp.WSGIServer):
    """WSGIServer with short timeout, so that server thread can stop this server."""

    def server_bind(self):
        basehttp.WSGIServer.server_bind(self)
        self.socket.settimeout(0.2)

    def get_request(self):
        try:
            sock, address = self.socket.accept()
            sock.settimeout(None)
            return (sock, address)
        except socket.timeout:
            raise

class WSGIRequestHandler(basehttp.WSGIRequestHandler):

    def log_message(self, format, *args):
        return

class RpcTestServerThread(threading.Thread):
    """Thread for running an http server while tests are running."""

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.stop_event = threading.Event()
        self.start_event = threading.Event()
        self.error = None
        super(RpcTestServerThread, self).__init__()
        self.daemon = True

    def start(self):
        super(RpcTestServerThread, self).start()
        self.start_event.wait()
        if self.error:
            raise self.error

    def run(self):
        """Sets up test server and loops over handling http requests."""
        try:
            handler = basehttp.AdminMediaHandler(WSGIHandler())
            server_address = (self.address, self.port)
            httpd = StoppableWSGIServer(server_address, WSGIRequestHandler)
            httpd.set_app(handler)
            self.start_event.set()
        except basehttp.WSGIServerException, e:
            self.error = e
            self.start_event.set()
            return

        # FIXME: This is broken if using SQLite and testing with an in memory
        # database, since SQLite won't share the connection between threads.

        # Loop until we get a stop event.
        while not self.stop_event.isSet():
            httpd.handle_request()

    def join(self, timeout=None):
        """Stop the thread and wait for it to finish."""
        self.stop_event.set()
        super(RpcTestServerThread, self).join(timeout)

class RpcTestCase(TransactionTestCase):
    """Base test case class for service tests."""

    # Note: Must inherit from TransactionTestCase instead of TestCase so that
    # the server thread and test client thread can use transactions and see
    # each other's changes to the database.

    def setUp(self):
        # FIXME: Create a test client with the same interface as Django's...
        for x in xrange(4):
            self.address = getattr(settings, 'PR_RPC_TEST_ADDR', None) or '127.0.0.1'
            self.port = int(getattr(settings, 'PR_RPC_TEST_PORT', None) or random.randint(8001, 65535))
            self.server_thread = RpcTestServerThread(self.address, self.port)
            try:
                self.server_thread.start()
                break
            except basehttp.WSGIServerException, e:
                try:
                    if e.args[0].args[0] in (13, 98, 99):
                        continue
                except (AttributeError, KeyError):
                    pass
                raise e
        # Modify the celery configuration to run tasks eagerly for unit tests.
        self._always_eager = conf.ALWAYS_EAGER
        conf.ALWAYS_EAGER = True

    def tearDown(self):
        conf.ALWAYS_EAGER = self._always_eager
        self.server_thread.join()

from tests_svc import *
