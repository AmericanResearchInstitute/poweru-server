# -*- coding: utf-8 -*-

import codecs
import csv
import cStringIO
import datetime
import hashlib
import logging
import os
import sys
import unicodedata
from django.db import transaction
from pr_services import exceptions
import facade

LOGGER_NAME = 'pr_services.utils'

logger = logging.getLogger(LOGGER_NAME)

class Utils(object):
    """Various utility functions needed for Power Reg classes."""

    @staticmethod
    def find_by_id(id, model_class):
        """
        Find a data object by primary key

        @param id           Primary key for the object
        @param model_class  a class derived from django.db.models.Model

        @return       Object instance
        """

        try:
            return model_class.objects.get(id=id)
        except model_class.DoesNotExist:
            raise exceptions.ObjectNotFoundException(model_class._meta.module_name, id)

    @staticmethod
    def merge_queries(q1, q2_manager, auth_token, q2_requested_fields, glue_field_name):
        """
        Merge the results of two queries.  For example, if you have a user query that includes
        lists of group primary keys, you may want to replace that list of groups PKs with a
        list of more meaningful information.  This function would take a result set like this:

        [{'username' : 'bob', 'groups' : [1,2]}]

        and turn it into this:

        [{'username' : 'bob', 'groups' : [{'id':1, 'name':'Jerks'}, {'id':2, 'name':'Schmucks'}]}]

        This function will also do the same replacement against a foreign key if
        one is passed instead of a list of FKs.

        You would do so with the following sort of code:

        q1 = user_manager.get_filtered(auth_token, {}, ['username', 'groups'])
        result_set = Utils.merge_queries(q1, GroupManager(), auth_token, ['name'], 'groups')

        :param q1:                  results of the primary call to get_filtered()
        :type q1:                   list
        :param q2_manager:          instance of a poweru manager
        :type q2_manager:           ObjectManager
        :param auth_token:          auth token
        :type auth_token:           string
        :param q2_requested_fields: list of field names you want for the secondary object
        :type q2_requested_fields:  list
        :param glue_field_name:     the name of the field in the q1 result set that should be
                                    merged with the secondary query
        :type glue_field_name:      string

        :return:                    q1 with contents of field specified by glue_field replaced
                                    with more detailed data from q2
        """

        # get a list of all pks for the secondary object
        q2_ids = set([])
        iterable_value = True
        for item in q1:
            value = item.get(glue_field_name, None)
            if value is None:
                continue
            try:
                value = iter(value)
                q2_ids |= set(value)
            except TypeError:
                iterable_value = False
                q2_ids.add(value)

        # execute a query for the secondary object
        q2 = q2_manager.get_filtered(auth_token,
            {'member' : {'id' : q2_ids}}, q2_requested_fields)
        q2_dict = {}
        for item in q2:
            q2_dict[item['id']] = item

        # replace PKs in q1 with data about the secondary object
        for item in q1:
            if iterable_value:
                new_list = []
                for key in item.get(glue_field_name, []):
                    new_list.append(q2_dict[key])
                item[glue_field_name] = new_list
            else:
                item[glue_field_name] = q2_dict[item[glue_field_name]]

        return q1

    @staticmethod
    def asciify(s):
        """Attempt to make a Unicode string into only ASCII characters, converting
        accented characters to their unaccented counterparts.

        This technique came from
        http://log.vaem.net/2008/06/python-translit-remove-accent.html

        It decomposes the string so that accented characters are represented
        by more than one character and then ignores non-ASCII characters.  For
        example, 'á' is converted to 'a' followed by a character that adds an
        acute accent to the previous character.  That second character is
        non-ASCII and gets stripped away.

        The routine ensures that the number of characters in the asciified
        string are the same as those in the original string to minimize information
        loss.

        @param s the string to convert
        @type s unicode
        @return a string with only ascii characters
        @rtype str

        """
        # make sure that s is a unicode object 
        s = unicode(s)
        asciified =  unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
        if len(s) != len(asciified):
            raise exceptions.AsciiConversionFailedException(s, asciified)
        return asciified

    @staticmethod
    def get_auth_token_object(auth_token_session_id, now=None):
        """This method gets an authentication token object for us from the auth_token_session_id.

        @param auth_token_session_id    The session_id of the auth_token we wish to fetch
        @type auth_token_session_id     str
        @param now                      The time that the request was made
        @type now                       datetime
        @return                         An auth_token object
        @rtype                          auth_token
        @raises                         exceptions.NotLoggedInException
        @raises                         exceptions.AuthTokenExpiredException

        """

        @transaction.autocommit
        def _consume_single_use_token(at):
            """
            helper method to atomically check that the token is unused and mark
            it used; needs to be in it's own function so we can declare the
            appropriate transaction semantics
            """
            # this update operation is expected to be atomic
            was_unused = facade.models.SingleUseAuthToken.objects.filter(
                id=at.id, used=False).update(used=True)
            return was_unused == 1


        if now is None:
            now = datetime.datetime.utcnow()

        try:
            at = facade.models.AuthToken.objects.get(session_id__exact=auth_token_session_id)
        except facade.models.AuthToken.DoesNotExist:
            raise exceptions.NotLoggedInException()
        if at.time_of_expiration < now:
            raise exceptions.AuthTokenExpiredException()
        at = at.downcast_completely()
        if isinstance(at, facade.models.SingleUseAuthToken) and \
                not _consume_single_use_token(at):
            raise exceptions.AuthTokenExpiredException()
        return at

    @staticmethod
    def unicode_csv_reader(unicode_csv_data, dialect='sanecsv', **kwargs):
        """This method (along with the utf_8_encoder() static method) are for reading CSV
        files encoded with UTF-8 correctly, which doesn't work right out
        of the box with the Python csv module.  They were taken from
        the Python 2.5 documentation at

        http://www.python.org/doc/2.5.2/lib/csv-examples.html#csv-examples

        """
        # csv.py doesn't do Unicode; encode temporarily as UTF-8:
        csv_reader = csv.DictReader(Utils.utf_8_encoder(unicode_csv_data),
            dialect=dialect, **kwargs)
        for row in csv_reader:
            # decode UTF-8 back to Unicode, cell by cell:
            for key in row.keys():
                if row[key] is not None:
                    row[key] = unicode(row[key], 'utf-8')
            yield row

    @staticmethod
    def utf_8_encoder(unicode_csv_data):
        """This is used along with the unicode_csv_reader() static method for reading
        in CSV data encoded in UTF-8, which doesn't work right out of the box
        with the Python csv module.  They were taken from the Python 2.5
        documentation at

        http://www.python.org/doc/2.5.2/lib/csv-examples.html#csv-examples

        """
        for line in unicode_csv_data:
            yield line.encode('utf-8')

    @staticmethod
    def _hash(input, hash_type):
        """Calculate a hash of input, using either SHA-1, or SHA-512

        @param input        The input to be hashed
        @param hash_type    The type of hash requested, either 'SHA-1' or 'SHA-512'
        @type hash_type     string
        @return             The hash of the input

        """
        # the SHA module needs plain byte strings to hash --
        # it chokes on unicode objects with non-ASCII characters
        if isinstance(input, unicode):
            input = input.encode('utf-8')

        if hash_type == 'SHA-1':
            s = hashlib.sha1()
        elif hash_type == 'SHA-512':
            s = hashlib.sha512()
        else:
            raise exceptions.InvalidUsageException('The requested hash type %s is not supported.  Please choose from SHA-1 or SHA-512.'%hash_type)

        s.update(input)
        return s.hexdigest()

    @staticmethod
    def _verify_hash(input, salt, hash_type, hash):
        """Hash the supplied credentials and verify them against the supplied hash

        @param input        input
        @type input        string
        @param salt         salt, which may be empty
        @type salt         string
        @param hash_type    name of hash type used
        @type hash_type    string
        @param hash         hash to which we will compare our calculated hash
        @type hash         string

        @return             True if there is a match else False
        @rtype              bool

        """
        assert hash_type in ['SHA-1', 'SHA-512'], \
            "unknown hash type %s" % (hash_type)
        pw_hash = Utils._hash(input + salt, hash_type)
        return bool(pw_hash == hash)

class UnicodeCsvWriter(object):
    """A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.

    From the Python 2.6 library documentation:
    http://docs.python.org/library/csv.html

    ARI Changes:

    * change class name from UnicodeWriter to UnicodeCsvWriter
    * make this explicitly a new-style class

    """
    def __init__(self, f, dialect='sanecsv', encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

class SaneCSV(csv.Dialect):
    """Describe the usual properties of sane CSV files.

    'sane CSV files' means comma-delimited, '"' as the field quoting character,
    '""' inside a field is an escapde '"' character, whitespace after the delimiter is ignored,
    windows line terminators, and QUOTE EVERYTHING!"""
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = True
    lineterminator = '\r\n'
    quoting = csv.QUOTE_ALL

# Registering the dialect here allows us to reference it by name, as long
# as utils is imported (or you're working in here).
csv.register_dialect("sanecsv", SaneCSV)


class TableData(object):
    """This class is used to represent rows of multi-column data in a nice
    text-based table

    """

    def __init__(self):
        self._rows = []

    def add_row(self, row):
        """All rows must have the same number of items, or columns

        :param row: an iterable with some number of table elements in order

        """
        self._rows.append(row)

    def clear(self):
        """ clear contents """
        self._rows = []

    @property
    def column_widths(self):
        """ return list of max widths for each column in the table """

        ret = []
        if len(self._rows):
            for index in range(len(self._rows[0])):
                ret.append(max([len(str(row[index])) for row in self._rows]))
        return ret

    def __str__(self):
        widths = self.column_widths
        banner = ''
        for count in range(sum(widths) + 3*(len(widths) - 1) + 7):
            banner += '#'
        banner += '\n'

        ret = '\n%s' % (banner)
        for row in self._rows:
            ret += '# '
            for index in range(len(row)):
                ret += str(row[index]).ljust(widths[index] + 3)
            ret += ' #\n'
        ret += banner
        return ret

class LazyImporter(object):
    """
    The LazyImporter class facilitates us in only importing attributes from
    modules when we are trying to use them from the facade.  This way, we can
    do things like writing facade.subsystems.Authorizer(), which will actually
    cause the Authorizer class to be imported the first time it is called.
    """
    def __init__(self):
        # Set up the import map, which maps attribute names to
        # their source module.
        self.import_map = dict()
        # Keep track of which attributes have been requested to be overriden
        # and in which modules the various incarinations of the attribute have
        # been defined.
        self.override_history = dict()

    def add_import(self, attribute_name, module_name):
        """Registers a facade attribute with a module name

        This method updates the import_map so that when something finally
        accesses this attribute on the facade, there is knowledge of what
        module contains the attribute in question.

        :param attribute_name: the attribute within the given module_name to
            lazily import
        :type attribute_name: string
        :param module_name: the name of the module, in Python dotted notation,
            from which to lazily import our desired attribute
        :type module_name: string

        """
        # By using a dictionary with managers as keys, overriding managers 
        # is done by calling "add_import" in variants.
        self.import_map[attribute_name] = module_name
        attr = LazyImportObjectProxy()
        setattr(self, attribute_name, attr)

    def override(self, attribute_name, module_name):
        """Lazily overrides an existing facade attribute

        This can be useful for when you need to override an attribute on the
        facade with something that subclasses the facade attribute you're about
        to override.  For example, when you need to override the Authorizer to
        add additional ACCheckMethods.

        When the attribute is finally accessed, the various incarnations of the
        attribute will be imported from all the modules that told us they
        defined it, in the order we were told.

        The first incarnation of the attribute should always come from
        pr_services, and should be added to the facade with add_import().
        The following incarnations of the attribute should always be added to
        the facade with override().

        Takes the same arguments as add_import().

        """
        old_attribute = object.__getattribute__(self, attribute_name)
        if isinstance(old_attribute, LazyImportObjectProxy):
            # not imported yet, do lazy override
            if attribute_name in self.override_history:
                self.override_history[attribute_name] += (self.import_map[attribute_name],)
            else:
                self.override_history[attribute_name] = (self.import_map[attribute_name],)
            # update the import map with the new module name
            self.import_map[attribute_name] = module_name
        else:
            # it's been imported already, too late to be lazy
            new_attr = self._get_attr_within_module(attribute_name, module_name)
            # update the import map for good measure
            self.import_map[attribute_name] = module_name
            setattr(self, attribute_name, new_attr)

    def eager_override(self, attribute_name, module_name):
        """Replaces a facade attribute eagerly (not lazily)

        This method is not recommended as override provides a laziness that is
        typically desireable.  But if eagerness is desired, this method
        provides that alternative.

        The first incarnation of the attribute should always come from
        pr_services, and should be added to the facade with add_import().
        The following incarnations of the attribute should always be added to
        the facade with eager_override().

        Takes the same arguments as add_import().

        """
        # By fetching the new attribute now, it has the opportunity to use an
        # existing facade attribute as a base class.
        new_attr = self._get_attr_within_module(attribute_name, module_name)
        # update the import map for good measure
        self.import_map[attribute_name] = module_name
        setattr(self, attribute_name, new_attr)

    def _get_attr_within_module(self, attribute_name, module_name):
        module = __import__(module_name, fromlist=[attribute_name])
        return getattr(module, attribute_name)

    def __getattribute__(self, name):
        """Only returns actual instances when they're referenced

        For attributes of the LazyImportObjectProxy type, this method will
        import the class defined by that object and then store the imported
        object on the attribute for future use.
        """
        # Get the attribute from the super class 
        # (i.e., do the traditional behavior for this method)
        attribute = object.__getattribute__(self, name)
        # If the attribute is a LazyImport object, let's actually import the
        # object and store it on the attribute
        if isinstance(attribute, LazyImportObjectProxy):
            # If this attribute has been overriden, we need to import all
            # incarnations of the attribute, in the order they were each added
            # to the facade to that when anyway subclassed a facade attribute,
            # they got the most recent one from their perspective.
            if name in self.override_history:
                for historic_module_name in self.override_history[name]:
                    new_value = self._get_attr_within_module(name, historic_module_name)
                    setattr(self, name, new_value)
            new_value = self._get_attr_within_module(name, self.import_map[name])
            # Let's set the new value to the attribute
            setattr(self, name, new_value)
            return new_value
        # If the object isn't a LazyImportObjectProxy, we assume it's the
        # actual requested instance and return it here.
        return attribute

class LazyImportObjectProxy(object):
    """
    This helps us to know whether we've imported the attribute for real yet or
    not.  Any attribute on a LazyImporter instance that is of this type has not
    truly been imported yet.
    """
    pass

# vim:tabstop=4 shiftwidth=4 expandtab
