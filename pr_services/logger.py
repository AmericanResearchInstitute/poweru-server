import logging
from django.conf import settings
import facade


def noop(*args, **kwargs):
    """
    """
    pass


class Logger(object):
    """
    Given a logger name and loglevel, logs messages.  If loglevel is not
    active, do as little work as possible.

    Can aggregate rows of related data that are useful to log as a table with
    nice formatting
    """

    def __init__(self, name, level):
        """
        :param name:    name of the logger as you would pass to logging.getLogger()
        :param level:   log level as you would pass to logging.setLevel()
        """

        if level < settings.LOGLEVEL:
            self.add_row = noop
            self.commit = noop
        else:
            self._logger = logging.getLogger(name)
            self._level = level
            self._table_data = facade.subsystems.TableData()

    def commit(self, message=None):
        """
        for a simple log statement, pass a message, and it will be logged.

        for table data, call this method with no arguments, and the rows that
        have been previously added will be logged in table format.  The table
        data will then be cleared

        :param message: text that should be logged
        """

        if message is None:
            self._logger.log(self._level, str(self._table_data))
            self._table_data.clear()
        else:
            self._logger.log(self._level, message)

    def add_row(self, row):
        """Add a row of data that will get formatted as a table when commited"""
        self._table_data.add_row(row)


