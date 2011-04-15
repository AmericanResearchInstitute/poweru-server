"""
Getters and setters for use in the object_manager
"""
__docformat__ = "restructuredtext en"

from datetime import datetime, date
import decimal
import logging
import cPickle
import urllib
import warnings
from django.conf import settings
from django.db import IntegrityError, connection
from django.db.models.fields import FieldDoesNotExist
from storage import UserPhotoStorage
import django.db
import django.db.backends.util
import django.db.models
import django.db.models.related
import exceptions
import facade
import pr_models
import pr_time
import tagging.models

def is_for_derived_attribute(func):
    """
    Decorator used to note that a getter is for a derived
    attribute.  This is needed by my static analysis tools
    to determine whether attributes exposed via the manager
    classes are derived.
    """
    
    func.is_for_derived_attribute = True
    return func

class Getter(object):
    logger = logging.getLogger('pr_services.getter')

    def __init__(self, auth_token, object_manager, django_query_set, requested_fields=None):
        if requested_fields is None:
            requested_fields = list()
        self.django_query_set = django_query_set
        self.object_manager = object_manager
        self.results = []
        # if 'id' isn't in the requested fields, it really should be!
        if 'id' not in requested_fields:
            requested_fields.append('id')
        for field in requested_fields:
            if field not in object_manager.getters:
                raise exceptions.FieldNameNotFoundException(field)
        self.authorizer = facade.subsystems.Authorizer()
        self.cache = {}
        # Create a dictionary of field names with method references to the appropriate getters
        self.getters = {}
        for f in requested_fields:
            try:
                self.getters.update( { f : getattr(self, self.object_manager.getters[f]) } )
            except AttributeError:
                raise exceptions.GetterNotFoundException(self.object_manager.getters[f])

        # If we are fetching any foreign key relationships, we can speed things up tremendously
        # by declaring them to django ahead of time in the select_related() call.
        foreign_keys = []
        for field_name in self.getters.keys():
            if self.object_manager.getters[field_name] in ['get_foreign_key', 'get_one_to_one']:
                foreign_keys.append(field_name)
        if foreign_keys:
            self.django_query_set = self.django_query_set.select_related(*foreign_keys)

        self.process(auth_token, requested_fields)

    def process(self, auth_token, requested_fields):
        for item in self.django_query_set:
            # Get the list of fields the the user is authorized to read from the authorizer
            authorized_fields = self.authorizer.get_authorized_attributes(auth_token, item, requested_fields, 'r')
            ret = {}
            for f in authorized_fields:
                ret[f] = self.getters[f](item, f)
            self.results.append(ret)

        # Trim empty dictionaries from the result set
        while {} in self.results:
            self.results.remove({})

    def get_general(self, result_object, field_name):
        try:
            return getattr(result_object, field_name)
        except AttributeError:
            self.logger.error('attribute %s not found on model %s' % (field_name, result_object._meta.module_name))
            raise exceptions.AttributeNotFoundException(field_name)

    @is_for_derived_attribute
    def get_final_type(self, result_object, field_name):
        """
        Returns the name of the class of the final type of the result_object.
        
        .. deprecated
        """
        
        warnings.warn("The get_final_type() getter is deprecated in favor of the get_content_type() getter. (ARI Redmine #2829)",
            DeprecationWarning, stacklevel=2)
        return result_object.downcast_completely().__class__.__name__
    
    @is_for_derived_attribute
    def get_content_type(self, result_object, field_name):
        """
        Returns a string representing an object's content type (using its final_type attribute to give
        the most specific one possible if present)
        """
        
        if isinstance(result_object, pr_models.PRModel):
            # we know exactly what the most specific type is -- use that
            return result_object.final_type.app_label + '.' + result_object.final_type.name
        else:
            # we only know what model the current instance is being referred to as, which
            # may not be the most specific type with multi-table inheritance.  Just return
            # a string of the same format as we would otherwise for the type in use.
            return result_object._meta.app_label + '.' + result_object._meta.object_name.lower()

    def get_time(self, result_object, field_name):
        """
        Gets a date/time value and convert it to an ISO8601 string.
        
        :param result_object: Instance of the django model in question
        :param field_name:    Name of the attribute we seek
        
        :return:              ISO8601 string
        """

        try:
            attr = getattr(result_object, field_name)
        except AttributeError:
            raise exceptions.FieldNameNotFoundException(field_name)
        if isinstance(attr, datetime):
            return attr.replace(microsecond = 0, tzinfo = pr_time.UTC()).isoformat()
        elif isinstance(attr, date):
            return attr.isoformat()

    @is_for_derived_attribute
    def get_mangled_id(self, result_object, field_name):
        try:
            getter_method = getattr(result_object, 'mangle_id')
            return getter_method(result_object.id)
        except AttributeError:
            raise exceptions.FieldNameNotFoundException(field_name)

    def get_many_to_one(self, result_object, field_name):
        """
        Gets the many side of a one-to-many relationship.
        """
        try:
            return getattr(result_object, field_name).all().values_list('id', flat = True)
        except AttributeError:
            raise exceptions.FieldNameNotFoundException(field_name)
        
    def get_many_to_many(self, result_object, field_name):
        """
        Gets a list of foreign keys for objects with which this object is related
        in a many-to-many relationship.

        The advantage we gain from this method is that it grabs the entire through
        table, caches it, and then can spit out m2m relationships for as many
        objects as we want very quickly.
        
        :param result_object: Instance of the django model in question
        :param field_name:    Name of the attribute we seek
        
        :return:              List of foreign keys for objects with which this object is related through
                              the requested many-to-many relationship.
        """

        my_id = result_object.id # We cache this reference to avoid tons of hash lookups
        # later during iteration

        # First, let's make sure we have have the matching data. If it's not already cached,
        # we'll go get it.
        if 'm2m' in self.cache and field_name in self.cache['m2m']:
            my_cache = self.cache['m2m'][field_name] # Remember, this is a reference, not a copy
        else:
            field = None
            try:
                field = self.object_manager.my_django_model._meta.get_field(field_name)
                table = field.m2m_db_table()
                my_column = field.m2m_column_name()
                foreign_column = field.m2m_reverse_name()
            except FieldDoesNotExist: # The field name doesn't exist, so we're probably accessing the far
                                      # end of the relationship. Let's try to come in the back way....
                for relation in self.object_manager.my_django_model._meta.get_all_related_many_to_many_objects():
                    if relation.get_accessor_name() == field_name:
                        field = relation.field
                        table = field.m2m_db_table()
                        foreign_column = field.m2m_column_name() # These are reversed, since we're
                                                                 # accessing the relationship from the
                                                                 # far end
                        my_column = field.m2m_reverse_name() # These are reversed, since we're accessing
                                                             # the relationship from the far end
                        break
            if not field: # If neither approach worked, the relationship doesn't exist as stated, and
                          # we're out of here!
                raise exceptions.FieldNameNotFoundException(field_name)
            if settings.DATABASE_ENGINE == 'oracle':
                # We need to make the column names upper case
                my_column = my_column.upper()
                foreign_column = foreign_column.upper()
                table = table.upper()
            max_name_length = connection.ops.max_name_length()
            my_column = django.db.backends.util.truncate_name(my_column, max_name_length)
            foreign_column = django.db.backends.util.truncate_name(foreign_column, max_name_length)
            table = django.db.backends.util.truncate_name(table, max_name_length)

            # Finally, the database work
            cursor = connection.cursor()
            query = "SELECT %s, %s from %s" % (my_column, foreign_column, table)
            cursor.execute(query)
            my_cache = cursor.fetchall()
            if 'm2m' not in self.cache:
                self.cache['m2m'] = {}
            self.cache['m2m'][field_name] = my_cache # Remember, this is a reference, not a copy

        # Now that we have the data, let's pick out the pieces we need
        ret = []
        for pair in my_cache:
            if pair[0] == my_id:
                ret.append(pair[1])

        return ret

    def get_address(self, result_object, field_name):
        ret = None
        if hasattr(result_object, field_name): 
            a = getattr(result_object, field_name)
            if isinstance(a, facade.models.Address):
                ret = { 'country' : a.country,
                        'region' : a.region,
                        'locality' : a.locality,
                        'postal_code' : a.postal_code,
                        'label' : a.label,
                }

        return ret

    @is_for_derived_attribute
    def get_photo_url(self, result_object, field_name):
        ret = None
        if hasattr(result_object, 'photo'):
            photo_filename = getattr(result_object, 'photo').name
            if photo_filename:
                ret = self.object_manager.photo_storage_engine.url(photo_filename)
        return ret

    @is_for_derived_attribute
    def get_session_price_from_training_voucher(self, result_object, field_name):
        return result_object.session_user_role_requirement.session.default_price

    @is_for_derived_attribute
    def get_user_names_from_rating(self, result_object, field_name):
        user = result_object.user
        return (user.first_name, user.last_name) if user else None

    @is_for_derived_attribute
    def get_choices_from_rating(self, result_object, field_name):
        return range(result_object.seek, result_object.seek + result_object.limit + 1)

    @is_for_derived_attribute
    def get_balance_from_training_unit_account(self, result_object, field_name):
        q = result_object.training_unit_transactions.values_list('value', flat=True)
        return result_object.starting_value + sum(q)

    def get_acl(self, result_object, field_name):
        if hasattr(result_object, field_name):
            attr = getattr(result_object, field_name)
            if attr:
                return cPickle.loads(attr)

    @is_for_derived_attribute
    def get_selection_from_rating_response(self, result_object, field_name):
        return result_object.selection + result_object.rating.seek

    def get_foreign_key(self, result_object, field_name):
        if hasattr(result_object, field_name):
            attr = getattr(result_object, field_name)
            if attr:
                return attr.id

    def get_one_to_one(self, result_object, field_name):
        """
        A one-to-one relationship works just like a foreign key relationship in Django, so we can just call the get_foreign_key.  We'll keep this method
        to avoid confusion.
        """
        return self.get_foreign_key(result_object, field_name)

    @is_for_derived_attribute
    def get_total_from_purchase_order(self, result_object, field_name):
        return result_object._get_total()

    @is_for_derived_attribute
    def get_is_paid_from_purchase_order(self, result_object, field_name):
        return result_object.is_paid

    @is_for_derived_attribute
    def get_used_value_from_training_unit_authorization(self, result_object, field_name):
        return result_object.get_used_value()
    
    @is_for_derived_attribute
    def get_session_user_role_requirements_from_user(self, result_object, field_name):
        surr_ids = facade.models.SessionUserRoleRequirement.objects.filter(assignments__user__id=result_object.id).values_list('id', flat=True)
        assignments = facade.models.Assignment.objects.filter(user__id=result_object.id, task__id__in=surr_ids)
        ret = []
        for assignment in assignments:
            ret.append({'status' : assignment.status, 'id' : assignment.task.id})
        return ret

    @is_for_derived_attribute
    def get_refunds_from_payment(self, result_object, field_name):
        ret = []
        for refund in result_object.refunds.all():
            ret.append( {
                    'amount' : refund.amount,
                    'date' : refund.blame.time.replace(microsecond=0,
                             tzinfo=pr_time.UTC()).isoformat(),
                    'transaction_id' : refund.transaction_id,
                    'result_message' : refund.result_message,
            })
        return ret

    @is_for_derived_attribute
    def get_date_from_blame(self, result_object, field_name):
        """
        Gets the creation date of any object which has a blame object
        """

        return result_object.blame.time.replace(microsecond=0, tzinfo=pr_time.UTC()).isoformat()

    def get_decimal(self, result_object, field_name):
        """
        Returns a string representation of a decimal field.
        
        :rtype: unicode or None
        """
        
        if hasattr(result_object, field_name):
            value = getattr(result_object, field_name)
            if value is not None:
                return unicode(getattr(result_object, field_name))
            else:
                return None
        else:
            raise exceptions.FieldNameNotFoundException(field_name)
        

    @is_for_derived_attribute
    def get_inventory_from_product(self, result_object, field_name):
        """
        Gets the current inventory for a product via a method on the product model
        
        :return: current product inventory level
        :rtype: int
        """
        return result_object.get_inventory()

    @is_for_derived_attribute
    def get_status_from_event(self, result_object, field_name):
        """
        Gets the status of an event by calling the event's get_status() method.
        
        :todo: ARI Redmine #2903 replace this with a property on the Event model
        
        :return: status of the event
        :rtype: string
        """
        
        if not isinstance(result_object, facade.models.Event):
            raise exceptions.InvalidActeeTypeException()

        return result_object.get_status()

    @is_for_derived_attribute
    def get_paypal_url_from_session(self, result_object, field_name):
        if not isinstance(result_object, facade.models.Session):
            raise exceptions.InvalidActeeTypeException()

        owner = result_object.event.owner
        if result_object.default_price > 0 and owner.enable_paypal and owner.paypal_address != None and len(owner.paypal_address):
            start = str(result_object.start)
            date_and_code = '%s, %s' % (start, result_object.name)
            if result_object.title != None:
                title = result_object.title
            elif result_object.event.title != None:
                title = result_object.event.title
            else:
                title = ''
            
            arguments = {   'amount' : str(decimal.Decimal(result_object.default_price) / decimal.Decimal(100)),
                            'business' : owner.paypal_address,
                            'cmd' : '_xclick',
                            'item_name' : '%s, %s' % (title[:125 - len(date_and_code)], date_and_code),
                            'no_shipping' : '2', # Require a shipping address
                        }
            return 'https://www.paypal.com/cgi-bin/webscr?%s' % (urllib.urlencode(arguments))

    @is_for_derived_attribute
    def get_tags(self, result_object, field_name):
        """ Gets the names of all the tags for an object. """
        tags = tagging.models.Tag.objects.get_for_object(result_object)
        tag_list = list()
        for tag in tags:
            tag_list.append(tag.name)
        return tag_list
    
    def get_tasks_from_task_bundle(self, result_object, field_name):
        """
        Returns an ordered list of dictionaries describing tasks in a
        task bundle.  The tasks are ordered by their corresponding
        presentation_order numbers.

        Additionally, it may be desirable to immediately present the
        next task to a user after completion of a task.  If so, the
        first task will have 'continue_automatically' set to True in
        the return value.

        Sample return value::
        
            [{'id': 3, 'presentation_order': 1, 'content_type': 'pr_services.video',
              'continue_automatically': False},
             {'id': 9, 'presentation_order': 2, 'content_type': 'pr_services.sco',
              'continue_automatically': True},
             {'id': 7, 'presentation_order': 3, 'content_type': 'pr_services.exam',
              'continue_automatically': False}]
         
        The content type is made from the final_type attribute of the tasks,
        using its app_label attribute, followed by a dot, followed by its name
        attribute.
        
        :todo: use content_type getter here
        """
        
        if not isinstance(result_object, facade.models.TaskBundle):
            raise exceptions.InvalidActeeTypeException()
        
        if field_name != 'tasks':
            raise exceptions.InvalidDataException('field_name must be "tasks"')
        
        associations = facade.models.TaskBundleTaskAssociation.objects.filter(
            task_bundle__id=result_object.id).order_by('presentation_order')
        
        ordered_task_list = []
        
        # the ternary expression for 'continue_automatically' is here
        # so that versions of Django <= 1.1 on MySQL won't result in
        # 1 or 0 being returned rather than True or False.  grrrr!
        for association in associations:
            ordered_task_list.append({'id': association.task.id,
                'presentation_order': association.presentation_order,
                'content_type': (association.task.final_type.app_label + '.' +
                                 association.task.final_type.name),
                'continue_automatically':
                    True if association.continue_automatically else False})
        
        return ordered_task_list

class Setter(object):
    logger = logging.getLogger('pr_services.setter')

    def __init__(self, auth_token, object_manager, django_object, setter_dict):
        self.object_manager = object_manager
        self.django_object = django_object
        self.setter_dict = setter_dict
        self.setters = {}
        for field in setter_dict:
            if field not in object_manager.setters:
                raise exceptions.FieldNameNotFoundException(field)
        self.authorizer = facade.subsystems.Authorizer()
        self.auth_token = auth_token
        self.authorizer.check_update_permissions(auth_token, django_object, setter_dict)
        for field in setter_dict:
            try:
                self.setters[field] = getattr(self, self.object_manager.setters[field])
            except KeyError:
                raise exceptions.FieldNameNotFoundException(field)
            except AttributeError:
                raise exceptions.SetterNotFoundException(self.object_manager.setters[field])

        self.process()

    def process(self):
        for field in self.setter_dict:
            self.setters[field](field, self.setter_dict[field])

    def set_address(self, field_name, address_value_dictionary):
        if hasattr(self.django_object, field_name): 
            a = getattr(self.django_object, field_name)
            if isinstance(a, facade.models.Address):
                setattr(self.django_object, field_name, None)
                self.django_object.save()
                a.delete()
        new_addr_dict = {}
        for key, value in address_value_dictionary.items():
            new_addr_dict[str(key)] = value if value is not None else u''
        new_a = facade.models.Address(**new_addr_dict)
        new_a.save()
        self.set_foreign_key(field_name, new_a.id)

    def set_decimal(self, field_name, value):
        """
        Set a decimal field, given a string representation of its value.
        
        :param field_name: name of the field to set
        :type field_name: string
        :param value: value represented as a string
        :type value: string
        """
        
        if field_name not in self.django_object._meta.fields:
            raise exceptions.FieldNameNotFoundException(field_name)
        
        if value in (None, ''):
            setattr(self.django_object, field_name, None)
        else:
            setattr(self.django_object, field_name, decimal.Decimal(value))
        
    def set_foreign_key(self, field_name, foreign_key):
        winning_field = None
        for field in self.django_object._meta.fields:
            if field.name == field_name:
                winning_field = field
                break
        if not winning_field:
            raise exceptions.FieldNameNotFoundException(field_name)
        foreign_model = winning_field.rel.to
        if foreign_key == None:
            foreign_instance = None
        else:
            foreign_instance = self.object_manager._find_by_id(foreign_key, foreign_model)
        setattr(self.django_object, field_name, foreign_instance)

    def set_one_to_one(self, field_name, foreign_key):
        """
        A one to one relationship works just like a foreign key relationship in Django, so we can just call the set_foreign_key.  We'll
        keep this method to avoid confusion.
        """
        return self.set_foreign_key(field_name, foreign_key)

    def set_general(self, field_name, new_value):
        try:
            setattr(self.django_object, field_name, new_value)
        except AttributeError:
            raise exceptions.FieldNameNotFoundException(field_name)

    def set_many(self, field_name, new_values):
        """
        This is a generic setter for use with models.ManyToManyField() relationships or the
        "many" end of a ForeignKey relationship.
        
        If you are setting a m2m relationship that has extra parameters by way of a 'through'
        table, you may specify those by making the items in the 'add' list dictionaries of their
        own. Each object being added is a dictionary with primary key indexed as 'id', and any
        other attributes of the relationship indexed by name.
        """

        def _cleanup_key(k):
            """Make sure primary key references are always ints."""
            if isinstance(k, dict):
                k['id'] = int(k['id'])
                return k
            else:
                return int(k)

        remove_keys = []
        # If we received a dictionary, make the appropriate assignments before processing
        if isinstance(new_values, dict):
            add_keys = map(_cleanup_key, new_values.get('add', []))
            remove_keys = map(_cleanup_key, new_values.get('remove', []))
        # If not, default to adding the keys we received
        else:
            add_keys = map(_cleanup_key, new_values)

        attribute = getattr(self.django_object, field_name)

        through_model = None
        # If this relationship uses a custom through table, the add() method will be missing
        if not hasattr(attribute, 'add'):
            through_model_name_or_reference = attribute.through
            if isinstance(through_model_name_or_reference, basestring):
                if through_model_name_or_reference == django.db.models.related.RECURSIVE_RELATIONSHIP_CONSTANT:
                    through_model = self.django_object.__class__    
                elif through_model_name_or_reference.find('.') != -1:
                    app_label, model_name = through_model_name_or_reference.split('.')
                else:
                    app_label = self.django_object.__class__._meta.app_label
                    model_name = attribute.through
                if through_model is None:
                    through_model = django.db.models.get_model(app_label, model_name, False)
            else:
                through_model = through_model_name_or_reference
            
            this_model = self.django_object.__class__
            other_model = attribute.model
            
            this_model_field_name = None
            other_model_field_name = None
            
            for field in through_model._meta.fields:
                if isinstance(field, django.db.models.fields.related.ForeignKey):
                    if issubclass(this_model, field.rel.to):
                        this_model_field_name = field.name
                    elif issubclass(other_model, field.rel.to):
                        other_model_field_name = field.name
            
            
            assert this_model_field_name is not None
            assert other_model_field_name is not None

        # Add things

        # We have to treat a many-to-one relationship differently, because the add() method
        # isn't as fancy (won't take foreign keys- only actual objects)
        if not hasattr(attribute, 'through'):
            # this is a many-to-one relationship
            add_objects = attribute.model.objects.in_bulk(add_keys).values()
            if len(add_objects) != len(add_keys):
                raise exceptions.ObjectNotFoundException(attribute.model)
            attribute.add(*add_objects)
        else:
            # this is a many-to-many relationship
            if through_model is None:
                attribute.add(*add_keys)
            else:
                for item in add_keys:
                    if isinstance(item, dict):
                        other_model_pk = item['id']
                    else:
                        other_model_pk = item
                    through_model_instance = through_model()
                    setattr(through_model_instance, this_model_field_name, self.django_object)
                    try:
                        foreign_object = other_model.objects.get(pk=other_model_pk)
                    except other_model.DoesNotExist:
                        raise exceptions.ObjectNotFoundException(other_model, other_model_pk)
                    # Set foreign end of glue table.django_object.id)
                    setattr(through_model_instance, other_model_field_name, other_model.objects.get(pk=other_model_pk))
                    # Now set the extra attributes of the relationship
                    if isinstance(item, dict):
                        extras = item.copy()
                        del extras['id']
                        self.authorizer.check_update_permissions(
                            self.auth_token, through_model_instance, extras)
                        for extra_attribute, extra_value in extras.iteritems():
                            if extra_attribute not in dir(through_model_instance):
                                raise exceptions.AttributeNotFoundException(extra_attribute)
                            field = through_model_instance._meta.get_field(extra_attribute)
                            # handle the case where we are updating a foreign key relationship and have a primary key
                            if isinstance(field, django.db.models.related.ForeignKey) and isinstance(extra_value, (int,long)):
                                setattr(through_model_instance, field.attname, extra_value)
                            # This handles most general types of relationships, plus a ForeignKey if the value we have is a Model instance
                            else:
                                setattr(through_model_instance, extra_attribute, extra_value)
                    through_model_instance.save()
                    self.authorizer.check_create_permissions(self.auth_token,
                        through_model_instance)
                    
        # Remove things
        if through_model is None:
            attribute.remove(*remove_keys)
        else:
            # we have a through table
            for key in remove_keys:
                try:
                    other_model_instance = other_model.objects.get(pk=key)
                    get_args = { this_model_field_name : self.django_object,
                                 other_model_field_name : other_model_instance, }
                    through_model_instance = through_model.objects.get(**get_args)
                    self.authorizer.check_delete_permissions(self.auth_token,
                        through_model_instance)
                    through_model_instance.delete()
                except other_model.DoesNotExist:
                    raise exceptions.ObjectNotFoundException(other_model, key)
                except through_model.DoesNotExist:
                    self.logger.debug('failed to find through table instance of model %s using parameters %s' % (through_model, get_args))
                    continue

    def set_time(self, field_name, new_value):
        if new_value:
            t = pr_time.iso8601_to_datetime(new_value)
        else:
            t = None
        setattr(self.django_object, field_name, t)

    def set_status(self, field_name, new_value):
        """
        Change the status of a Django object that has a change_status
        method.  This uses PRModel.downcast_completely
        to simulate model polymorphism, thereby using subclasses' implementations
        of the change_status method even when given an instance of a superclass
        that happens to also correspond to an instance of a subclass.
        
        :param field_name: unused
        :param new_value: new status value
        :type new_value: string
        """
        
        # make the object polymorphic, so that the most specific
        # implementation of its change_status method gets used 
        if hasattr(self.django_object, 'downcast_completely'):
            self.django_object = self.django_object.downcast_completely()
        self.django_object.change_status(new_value)

    def set_acl(self, field_name, new_value):
        setattr(self.django_object, field_name, cPickle.dumps(new_value))
    
    def set_forbidden(self, field_name, new_value):
        """
        This simply disallows the setting of an attribute, raising an
        OperationNotPermittedException
        """

        raise exceptions.OperationNotPermittedException()

    def set_tags(self, field_name, new_value):
        """
        Modifies the tags for a given object.
        
        :param field_name: this is ignored
        :type field_name: string
        :param new_value: a dictionary with an 'add' or 'remove' key
        :type new_value: dict
        
        If ``new_value`` has a key named 'add', that key must point to a list
        of tag names to add.  Likewise, if it has a key named 'removed',
        that key must point to a list of tag names to remove.
        """
        
        if isinstance(new_value, dict):
            tags_to_add = None
            tags_to_remove = None
            if new_value.has_key('add'):
                if isinstance(new_value['add'], list):
                    tags_to_add = new_value['add']
                else:
                    raise exceptions.InvalidDataException('expected a list of tags to add')
            if new_value.has_key('remove'):
                if isinstance(new_value['remove'], list):
                    tags_to_remove = new_value['remove']
                else:
                    raise exceptions.InvalidDataException('expected a list of tags to remove')
            if tags_to_add is not None:
                for tag in tags_to_add:
                    # for #1922, add quotes to tag name to handle multi-word tags.
                    tagging.models.Tag.objects.add_tag(self.django_object, '"%s"' % tag)
            if tags_to_remove is not None:
                current_tags = tagging.models.Tag.objects.get_for_object(self.django_object)
                new_tag_names = list()
                for tag in current_tags:
                    if tag.name not in tags_to_remove:
                        new_tag_names.append(tag.name)
                tagging.models.Tag.objects.update_tags(self.django_object, '')
                for tag_name in new_tag_names:
                    # for #1922, add quotes to tag name to handle multi-word tags.
                    tagging.models.Tag.objects.add_tag(self.django_object, '"%s"' % tag_name)
        else:
            raise exceptions.InvalidDataException(
                'input to the set_tags() setter must be a dictionary')
            
    def set_tasks_for_task_bundle(self, field_name, new_value):
        """
        Replaces the task associations for a task bundle with a new set of task
        associations.
        
        Nota bene:
        
        Because this function replaces the task associations for a task bundle,
        a race condition is possible where one user adds a task to the
        task bundle after another user has read the contents of a task bundle.
        If the user who has just read the (old) contents of the task bundle
        then adds a different task to it, the previous update is lost.
        
        :param field_name: the name of the field to set
        :type field_name: string
        :param new_value: ordered list of tasks to associate with this
            task bundle, replaces previous associations
        :type new_value: list
        
        The structure of the new_value field should be almost exactly the same
        as the structure of the return value given by
        Getter.get_tasks_from_task_bundle.  However, the 'content_type'
        attributes are not required (and are ignored if present).  Additionally,
        the items do not need to be ordered by presentation_order.  If
        'continue_automatically' is not specified, False will be assumed.
        
        Example new_value::
        
            [{'id': 3, 'presentation_order': 3, 'continue_automatically': False},
            {'id': 9, 'presentation_order': 1, 'continue_automatically': True},
            {'id': 7, 'presentation_order': 2, 'continue_automatically': False}]
            
        """
        
        self.django_object.tasks.clear()
        for association in new_value:
            if (not isinstance(association, dict) or 'id' not in association or
                'presentation_order' not in association):
                raise exceptions.InvalidDataException('expected a list of dictionaries, each with "id" and ' +\
                    '"presentation_order" keys')
            continue_automatically = association.get('continue_automatically', False)
            facade.models.TaskBundleTaskAssociation.objects.create(
                task_id=association['id'], task_bundle=self.django_object,
                presentation_order=association['presentation_order'],
                continue_automatically=continue_automatically)

# vim:tabstop=4 shiftwidth=4 expandtab
