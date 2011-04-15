"""
@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from datetime import datetime
import sys
from utils import Utils
from xml import dom
from xml.dom import minidom
from xml.etree import ElementTree
from xml.parsers import expat
import csv
import exceptions
import facade

class ImportManager(object):
    """
    Import data from CSV. The first row should define the attribute names for the columns. For boolean
    values, use '1' and '0'.  See the appropriate _manager.create()
    method for details on field types and descriptions.
   
    For each method, csv_data is a foreign key for a csv_data object.  Those are
    created by uploading a text file to upload_csv/ with a POST request, and the
    auth_token variable passed with name 'auth_token'.  When the request is
    successful (200 response code), a key value will be returned.
    """

    def __init__(self):
        self.session_template_manager = facade.managers.SessionTemplateManager()
        self.event_manager = facade.managers.EventManager()
        self.session_manager = facade.managers.SessionManager()
        self.user_manager = facade.managers.UserManager()
        self.organization_manager = facade.managers.OrganizationManager()
        self.venue_manager = facade.managers.VenueManager()
        self.region_manager = facade.managers.RegionManager()
        self.room_manager = facade.managers.RoomManager()
        self.exam_manager = facade.managers.ExamManager()

    def import_session_templates(self, auth_token, csv_object, interactive=False):
        """
        Common method to import session_templates from csv data
        
        @param csv_object   A csv_data object.  Every field should be in double quotes.
        @return             A list of primary keys for the newly created session_templates
        """
        # These are the fields that are required in order to import a SessionTemplate object
        required_session_template_fields = ['shortname', 'fullname', 'version', 'description', 'price', 'lead_time', 'active']

        # the True value makes it leave the \n character on the ends of lines
        lines = csv_object.text.splitlines(True)
        reader = Utils.unicode_csv_reader(lines)
        keys = [] # Store primary keys of newly created session_templates here
        line_num = 1 # keep track of which line we're on
        exception_message = '' # If we get exceptions, we just add them to this string and keep going, so we can report all the problems at the end
        for row in reader:
            line_num += 1
            self._form_create_dict(auth_token, row, required_session_template_fields)
            try:
                c = self.session_template_manager._create(**row)
                keys.append(c.id)
            except ValueError, ve:
                if len(exception_message):
                    exception_message += '\n'
                exception_message += 'line ' + str(line_num) + ': ValueError:' + str(ve)
            except exceptions.InvalidDataException, ide:
                if len(exception_message):
                    exception_message += '\n'
                exception_message += 'line ' + str(line_num) + ': ' + str(ide)
            except facade.models.ModelDataValidationError, ve:
                if len(exception_message):
                    exception_message += '\n'
                exception_message += 'line ' + str(line_num) + ': ValidationError: ' + str(ve)

        if len(exception_message):
            raise exceptions.InvalidDataException(exception_message)
        return keys
        
    def import_sessions(self, auth_token, csv_data, interactive=False):
        """
        Common method for importing sessions from csv data
        
        @param csv_data A csv_data object. Every field should be in double quotes.
        @return         A list of primary keys for the newly created Sessions
        """
        # These are the fields that are required in order to import a Session object
        required_session_fields = ['start', 'end', 'status', 'confirmed', 'default_price', 'event']
        required_event_fields = ['name_prefix', 'title', 'description', 'start', 'end', 'organization', 'product_line']

        # the True value makes it leave the \n character on the ends of lines
        lines = csv_data.text.splitlines(True)
        csv_object = None # Garbage collection?
        reader = Utils.unicode_csv_reader(lines)
        keys = {} # Store primary keys of newly created sessions and events here
        keys['sessions'] = []
        keys['events'] = []
        line_num = 1
        events_created = {} # Store primary keys of the events as they are created, indexed by the 'unique_identifier'
        exception_message = '' # If we get exceptions, we just add them to this string and keep going, so we can report all the problems at the end
        for row in reader:
            line_num += 1
            event_fields = self._get_model_fields(row, 'event')
            unique_event_identifier = event_fields.pop('unique_identifier')
            if unique_event_identifier not in events_created:
                # Create the event
                self._form_create_dict(auth_token, event_fields, required_event_fields)
                try:
                    new_event = self.event_manager.create(**event_fields)
                    keys['events'].append(new_event.id)
                    events_created[unique_event_identifier] = new_event.id
                except ValueError, ve:
                    if len(exception_message):
                        exception_message += '\n'
                    exception_message += 'line ' + str(line_num) + ': ValueError:' + str(ve)
                    break
                except exceptions.InvalidDataException, ide:
                    if len(exception_message):
                        exception_message += '\n'
                    exception_message += 'line ' + str(line_num) + ': ' + str(ide)
                    break
                except facade.models.ModelDataValidationError, ve:
                    if len(exception_message):
                        exception_message += '\n'
                    exception_message += 'line ' + str(line_num) + ': ValidationError: ' + str(ve)
                    break

            session_fields = self._get_model_fields(row, 'session')
            session_fields['event'] = events_created[unique_event_identifier]
            self._form_create_dict(auth_token, session_fields, required_session_fields)
            try:
                s = self.session_manager.create(**session_fields)
                keys['sessions'].append(s.id)
            except ValueError, ve:
                if len(exception_message):
                    exception_message += '\n'
                exception_message += 'line ' + str(line_num) + ': ValueError:' + str(ve)
            except exceptions.InvalidDataException, ide:
                if len(exception_message):
                    exception_message += '\n'
                exception_message += 'line ' + str(line_num) + ': ' + str(ide)
            except facade.models.ModelDataValidationError, ve:
                if len(exception_message):
                    exception_message += '\n'
                exception_message += 'line ' + str(line_num) + ': ValidationError: ' + str(ve)

        if len(exception_message): # If we had any exceptions, let's tell the user about them now
            raise exceptions.InvalidDataException(exception_message)

        return keys

    def import_users(self, auth_token, csv_data, interactive=False):
        """
        Common method to import users from csv data
        
        @param csv_data   A csv_data object.
        @return           A list of primary keys for the newly created users
        """
        def _handle_user_addresses_in_row_and_fill_in_passwords(row):
            """
            Pick out fields related to addresses and organize them accordingly.
            """
            shipping_address_fields, other_fields = self._separate_fields_of_prefix(row, 'shipping_address_')
            billing_address_fields, remaining_fields = self._separate_fields_of_prefix(other_fields, 'billing_address_')
            if len(shipping_address_fields):
                remaining_fields['shipping_address'] = shipping_address_fields
            if len(billing_address_fields):
                remaining_fields['billing_address'] = billing_address_fields
            if len(remaining_fields['initial_password']) == 0:
                remaining_fields['initial_password'] = self.user_manager._generate_random_string(16)
                remaining_fields['send_password'] = True

            return remaining_fields

        required_fields = ['username', 'initial_password', 'title', 'first_name', 'last_name', 'phone', 'email', 'status']
        special_fields = {
            'groups' : {
                'field_type' : 'many_to_many',
                'lookup_by' : 'name',
                'model_name' : 'Group',
            },
            'organizations' : {
                'field_type' : 'many_to_many',
                'lookup_by' : 'name',
                'model_name' : 'Organization',
            },
        }
        return self._import_from_csv(auth_token, csv_data, self.user_manager,
                                     required_fields, _handle_user_addresses_in_row_and_fill_in_passwords,
                                     special_fields, interactive=interactive)

    def import_venues(self, auth_token, csv_data, interactive=False):
        """
        Import venues from CSV data.
        
        @param auth_token
        @type auth_token    models.AuthToken
        @param csv_data     A csv_data object.
        @type csv_data      models.csv
        @return             A list of primary keys for the newly created venues
        @rtype              list of int
        """
        required_fields = ['name', 'phone', 'region']
        special_fields = {
            'region': {
                'field_type': 'foreign_key',
                'lookup_by': 'name',
                'model_name': 'Region'}
            }
        return self._import_from_csv(auth_token, csv_data, self.venue_manager,
                                     required_fields, self._assemble_address_in_row,
                                     special_fields, interactive=interactive)

    def import_organizations(self, auth_token, csv_data, interactive=False):
        """
        Import organizations from CSV data.
        
        @param auth_token
        @type auth_token    models.AuthToken
        @param csv_data     A csv_data object.
        @type csv_data      models.csv
        @return             A list of primary keys for the newly created organizations
        @rtype              list of int
        """
        required_fields = ['name']
        return self._import_from_csv(auth_token, csv_data, self.organization_manager,
                                     required_fields, self._assemble_address_in_row, interactive=interactive)

    def _assemble_address_in_row(self, row):
        """
        For any object with an Address model associated as 'address', this method will
        pick out fields prefixed with 'address' and assemble them into a dictionary
        that can be processed by the create() method.
        """
        address_fields, other_fields = self._separate_fields_of_prefix(row, 'address_')
        if len(address_fields):
            other_fields['address'] = address_fields
        return other_fields

    def _import_from_csv(self, auth_token, csv_data, manager, required_fields,
        custom_row_function=None, special_fields=None, interactive=False):
        """
        Generic method to import CSV data and run it through the create() method
        of a manager.
        
        @param csv_data             A csv_data object
        @type  csv_data             models.csv
        @param manager              Instance of manager that corresponds to the
                                    object being created
        @type  manager              ObjectManager
        @param required_fields      list of field names which are required by
                                    the create() method
        @type  required_fields      list
        @param custom_row_function  optional function that takes a row
                                    dictionary as an argument and returns a row
                                    dictionary.  If you need to manipulate each
                                    row in any way, this is the place to do it.
        @type  custom_row_function  function
        @param special_fields       optional dictionary defining special fields
                                    on the manager and how they should be
                                    translated. This is particularly useful for
                                    establishing many to many relationships in a
                                    CSV.
        @type  special_fields       dict

        @return                     list of primary keys for newly created
                                    objects
        @rtype                      list of integers
        """



        # the True value makes it leave the \n character on the ends of lines
        lines = csv_data.text.splitlines(True)
        csv_data = None # Garbage collection?
        reader = Utils.unicode_csv_reader(lines)
        keys = [] # Store primary keys of newly created venues here
        line_num = 1
        exception_details = {}  # If we get exceptions, add a new entry to this
                                # dictionary for each line.
        for row in reader:
            line_num += 1
            try:
                if custom_row_function is not None:
                    row = custom_row_function(row)
                self._form_create_dict(auth_token, row, required_fields,
                    special_fields)
                v = manager.create(**row)
                keys.append(v.id)
                if interactive:
                    sys.stderr.write('.')
            except ValueError, ve:
                exception_details[line_num] = u'ValueError: %s' % unicode(ve)
                if interactive:
                    sys.stderr.write('E')
                    print >> sys.stderr, "\nline %d: [%s]" % (line_num,
                        exception_details[line_num])
                    print >> sys.stderr, '\n', row, '\n'
            except exceptions.InvalidDataException, ide:
                exception_details[line_num] = unicode(ide)
                if interactive:
                    sys.stderr.write('E')
                    print >> sys.stderr, "\nline %d: [%s]" % (line_num,
                        exception_details[line_num])
                    print >> sys.stderr, '\n', row, '\n'
            except facade.models.ModelDataValidationError, ve:
                exception_details[line_num] = u'ValidationError: %s' % unicode(ve)
                if interactive:
                    sys.stderr.write('E')
                    print >> sys.stderr, "\nline %d: [%s]" % (line_num,
                        exception_details[line_num])
                    print >> sys.stderr, '\n', row, '\n'
            except Exception, e:
                exception_details[line_num] = unicode(e)
                if interactive:
                    sys.stderr.write('E')
                    print >> sys.stderr, "\nline %d: [%s]" % (line_num,
                        exception_details[line_num])
                    print >> sys.stderr, '\n', row, '\n'

        # If we had any exceptions, let's tell the user about them now.
        if len(exception_details):
            ide = exceptions.InvalidDataException('%d items could not be imported' % \
                len(exception_details))
            ide.details.update(exception_details)
            raise ide

        return keys

    def import_regions(self, auth_token, csv_data, interactive=False):
        """
        Import regions from CSV data.
        
        @param auth_token
        @type auth_token    models.AuthToken
        @param csv_data     A csv_data object.
        @type csv_data      models.csv
        @return             A list of primary keys for the newly created regions
        @rtype              list of int
        """
        required_fields = ['name']
        return self._import_from_csv(auth_token, csv_data, self.region_manager,
            required_fields, interactive=interactive)

        csv_object = self._upload_security_common(auth_token, csv_data_id)
        # the True value makes it leave the \n character on the ends of lines
        lines = csv_object.text.splitlines(True)
        csv_object = None # Garbage collection?
        reader = Utils.unicode_csv_reader(lines)
        keys = [] # Store primary keys of newly created venues here
        line_num = 1
        #: cache regions from the database
        region_cache = {}
        for row in reader:
            name = row[0]
            r = self.region_manager.create(auth_token, name)
            keys.append(r.id)
            line_num += 1
        return keys


    def import_rooms(self, auth_token, csv_data, interactive=False):
        """
        Common method for importing venues from csv data
        
        @param csv_data   A foreign key for a csv_data object as returned from a POST
                request to upload_csv/. Every field should be in double quotes.
                Fields in order are: name, venue (foreign key), capacity

        @return           A list of primary keys for the newly created venues
        """

        csv_object = self._upload_security_common(auth_token, csv_data)
        # the True value makes it leave the \n character on the ends of lines
        lines = csv_object.text.splitlines(True)
        csv_object = None # Garbage collection?
        reader = Utils.unicode_csv_reader(lines)
        keys = [] # Store primary keys of newly created venues here
        line_num = 0
        for row in reader:
            try:
                v = self.room_manager.create(auth_token, row[0], row[1], row[2])
            except ValueError, ve:
                raise exceptions.InvalidDataException('line ' + str(line_num) +
                    ': ValueError:' + str(ve))
            except exceptions.InvalidDataException, ide:
                raise exceptions.InvalidDataException('line ' + str(line_num) +
                    ': ' + str(ide))

            keys.append(v.id)
            line_num += 1
        return keys

    def _form_create_dict(self, auth_token, row_dict, required_fields, special_fields=None):
        """
        Remove fields that are not required from the row_dict, and add them to a new dictionary indexed in the row dict as optional_parameters

        @param row_dict         A dictionary representing a single row from the CSV file being imported
        @type row_dict          dict
        @param required_fields  A list of field names that are required for the object being imported.  If the method finds a field in the row_dict that is not in this list,
                                that field will be removed from row_dict and added to the return value
        @param special_fields   A dictionary defining special fields on the manager and how they should be translated.  This is particularly useful for establishing many to
                                many relationships in a CSV.  An example:

                                special_user_fields = {
                                    'groups' : {
                                        'field_type' : 'many_to_many',
                                        'lookup_by' : 'name',
                                        'model_name' : 'Group'
                                    },
                                }
        """
        if special_fields is None:
            special_fields = {}
        options_dict = {}
        for key in row_dict.keys():
            if key in special_fields:
                # If the key is found in the special fields, we'll need to do a lookup first to replace the object with a primary key
                if special_fields[key].get('field_type', '') == 'many_to_many':
                    # We have a many to many relationship - look up the fields in our DB to find the primary keys, and build a list of them
                    foreign_objects = row_dict[key].split(',')
                    foreign_keys = []
                    for foreign_object in foreign_objects:
                        # Find the primary key of foreign_object
                        django_model = getattr(facade.models, special_fields[key]['model_name'])
                        filter_kw_args = {special_fields[key]['lookup_by']+'__exact' : foreign_object}
                        foreign_keys.append(django_model.objects.get(**filter_kw_args).id)
                    row_dict[key] = foreign_keys
                elif special_fields[key].get('field_type', '') == 'foreign_key':
                    # We have a foreign key - look up the field to find the primary key of the foreign object.
                    if not row_dict[key].strip():
                        row_dict[key] = None
                    else:
                        django_model = getattr(facade.models, special_fields[key]['model_name'])
                        filter_kw_args = {special_fields[key]['lookup_by']+'__exact' : row_dict[key]}
                        row_dict[key] = django_model.objects.get(**filter_kw_args).id
                else:
                    raise exceptions.InternalErrorException('field_type %s in special fields import not recognized'%special_fields[key].get('field_type', ''))
            elif '__' in key:
                raise NotImplementedError, 'cannot yet lookup foreign keys by name'

            if key not in required_fields:
                options_dict[key] = row_dict.pop(key)

        row_dict['optional_attributes'] = self._remove_undef_options(options_dict)
        row_dict['auth_token'] = auth_token

    def _separate_fields_of_prefix(self, row_dict, prefix):
        """
        Separate a dictionary into two new dictionaries: one for items whose key starts with the prefix,
        and one for all of the others. Items in the former have the prefix removed from their key.

        @param row_dict     row in dictionary form
        @type  row_dict     dict
        @param prefix       prefix that should be sorted on and stripped
        @type  prefix       string
        @return             dictionary of items formerly prefixed by prefix, and dictionary of all other items
        @rtype              two dictionaries
        """
        prefix_items = {}
        other_items = {}
        for item in row_dict:
            if item.startswith(prefix):
                prefix_items[item[len(prefix):]] = row_dict[item]
            else:
                other_items[item] = row_dict[item]

        return prefix_items, other_items

    def _get_model_fields(self, row_dict, model):
        """
        For some of the models we import, such as sessions and events, there are columns for more than one model in the csv file that are prepended with the model name.  This
        method takes the dictionary representing the CSV row, and looks for the keys that belong to the model specified by the parameter "model", and returns those key value
        pairs in a new dictionary, removing the model name from the keys.

        @param row_dict A row from the CSV, in dictionary form
        @type row_dict  dictionary
        @param model    The name of the model we are trying to separate from the row_dict
        @type model     string
        @return         A dictionary representing the fields from row_dict that pertain to model, removing "%s_"%model from the front of the keys
        """
        model_dict = {}
        for key in row_dict.keys():
            split_key = key.partition('_')
            if split_key[0] == model:
                model_dict[split_key[2]] = row_dict[key]
        return model_dict

    def _remove_undef_options(self, options):
        """
        Make a copy of the options and include only defined values
        """

        ret = {}
        for option in options:
            if options[option] not in (None, ''):
                ret[option] = options[option]
        return ret

    def import_exam(self, auth_token, exam_xml):
        return self.exam_manager.create_from_xml(auth_token, exam_xml)

    def _import_ac_check_methods(self, xml_text):
        """
        Import the list of ac_check_methods with attributes that will be stored in
        the database for frontend use
        
        @param        xml_text    A string containing the XML in question
        """

        try:
            tree = ElementTree.XML(xml_text)
            for method in tree:
                m = facade.models.ACCheckMethod()
                m.name = method.attrib['name']
                m.title = method.attrib['title']
                m.description = method.attrib['description']
                m.save()
        except expat.ExpatError:
            raise exceptions.InvalidDataException("xml input is not valid")
        except KeyError:
            raise exceptions.InvalidDataException("xml input is not valid")

# vim:tabstop=4 shiftwidth=4 expandtab
