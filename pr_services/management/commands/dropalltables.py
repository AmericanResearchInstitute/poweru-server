import django.db

from django.core.management.base import NoArgsCommand
from django.db import connection, transaction, backend

class Command(NoArgsCommand):
    requires_model_validation = False

    def handle_noargs(self, **options):
        cursor = connection.cursor()
        engine = django.db.database['ENGINE']

        if engine == 'django.db.backends.postgresql_psycopg2':
            handler = _PostgresEngineHandler(cursor)
        elif engine == 'django.db.backends.mysql':
            handler = _MysqlEngineHandler(cursor)
        elif engine == 'django.db.backends.oracle':
            handler = _OracleEngineHandler(cursor)
        else:
            handler = _BaseEngineHandler(cursor)

        transaction.enter_transaction_management()

        handler.pre_removal()

        for table_name in handler.table_names:
            print "Dropping table %s" % table_name
            handler.drop_table(table_name)

        handler.post_removal()

        transaction.commit()

# Handler classes, 
class _BaseEngineHandler(object):
    # Should work with sqlite and the dummy backends, or anything else that
    # doesn't need special hand holding
    def __init__(self, cursor):
        self.cursor = cursor
        self.table_names = connection.introspection.get_table_list(cursor)

    def drop_table(self, table_name):
        self.cursor.execute('DROP TABLE %s' % table_name)

    def pre_removal(self):
        pass

    def post_removal(self):
        pass

class _MysqlEngineHandler(_BaseEngineHandler):
    # Uses a "normal" drop statement, so the handler takes care of FK checks
    def pre_removal(self):
        self.cursor.execute('SET FOREIGN_KEY_CHECKS = 0')

    def post_removal(self):
        self.cursor.execute('SET FOREIGN_KEY_CHECKS = 1')

class _OracleEngineHandler(_BaseEngineHandler):
    # Oracle does not make things simple...
    def pre_removal(self):
        # Clean out the sequences for our models before we drop the tables
        for table_name in self.table_names:
            drop_statement = 'DROP SEQUENCE %s' % backend.get_sequence_name(table_name)
            try:
                self.cursor.execute(drop_statement)
                print "Dropping sequence %s" % table_name
            except backend.DatabaseError, e:
                # Some tables don't have sequences.
                # Match the error - "ORA-02289: sequence does not exist"
                if 'ORA-02289' in str(e.args[0]):
                    print 'Table %s had no sequence to delete.' % table_name
                else:
                    raise

    def post_removal(self):
        # Since we can't throw a 'PURGE' on DROP SEQUENCE, we'll just
        # clean up the whole recycle bin here. Ugly, but gets the job done
        print 'Purging Oracle Recycle Bin'
        self.cursor.execute('PURGE RECYCLEBIN')

    def drop_table(self, table_name):
        self.cursor.execute('DROP TABLE %s CASCADE CONSTRAINTS' % table_name)

class _PostgresEngineHandler(_BaseEngineHandler):
    def drop_table(self, table_name):
        self.cursor.execute('DROP TABLE %s CASCADE' % table_name)

