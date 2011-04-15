"""
Logging for the e-commerce Django app.

@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2008 American Research Institute, Inc.
"""

from e_settings import *
import datetime
import sys
import os
import traceback

from django.core.mail import mail_admins

if DATABASE_ENGINE == 'mysql':
    import MySQLdb as db_api
elif DATABASE_ENGINE == 'sqlite3':
    import sqlite3 as db_api

from exceptions import database_error_exception

def db_connect():
    if DATABASE_ENGINE == 'sqlite3':
        cx = db_api.connect(DATABASE_NAME)
        cx.isolation_level = None # Forces autocommit
    elif DATABASE_ENGINE == 'mysql':
        cx = db_api.connect(DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD, DATABASE_NAME)
    else:
        raise Exception("unsupported database engine %s" % (DATABASE_ENGINE))
    return cx

class raw_response:
    """
    Take the raw response as sent from a merchant services gateway
    and stick it directly into a database, just in case something goes
    wrong while the application is processing the response.
    
    Use a database that is on a separate host from the rest of the app.
    
    You should instantiate this class before initiating communication
    with the merchant services gateway, and run enter() immediately after.

    We assume that the database API in use is compliant with PEP-249 V2.0
    """

    def __init__(self, text = ''):
        """
        constructor
        
        @param text   Whatever text was directly passed by the merchant services gateway.
        @type text str
        """

        #: whatever text was directly passed by the merchant sevices gateway
        self.text = text

        try:
            self.db = db_connect()
            self.cursor = self.db.cursor()
        except db_api.Error, s:
            raise database_error_exception('Database Error %s: %s' % (s[0], s[1]))

    def enter(self):
        """
        Insert the contents of self.text into the database.
        """

        now_str = str(datetime.datetime.utcnow().replace(microsecond=0))

        # These are standard labels defined in PEP-249
        if db_api.paramstyle == 'qmark':
            sql_statement = """INSERT INTO raw_response (text, time) VALUES (?, ?);"""
        elif db_api.paramstyle == 'format':
            sql_statement = """INSERT INTO raw_response (text, time) VALUES (%s, %s);"""

        try:
            self.cursor.execute(sql_statement, (self.text, now_str))
        except db_api.Error, e:
            self.silently_handle_error(e)

    def silently_handle_error(self, exception):
        """
        Send an email to an admin with the contents of args and self.text.
        
        @param exception   an exception that was thrown
        @type exception Exception
        """

        message_body = u"""An external e-commerce error has occurred.

Response text was likely not stored in the database.

Exception details:
%s

reponse text:
[%s]

absolute path of this instance: %s
""" % (traceback.format_exc(exception), self.text, self._get_instance_path())
        mail_admins('e-commerce error', message_body)
        
    def _get_instance_path(self):
        """
        Returns the absolute path of the Django project that this app is in, provided
        that the app is installed as files and isn't an egg or anything like that.
        
        This isn't pretty, but I need a way to identify which instance these errors
        are coming from, and this is the only useful way that I know.
        """

        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
# vim:tabstop=4 shiftwidth=4 expandtab
