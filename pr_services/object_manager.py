"""
abstract base class for classes that manage persistent objects in the Power Reg 2 system
"""
__docformat__ = "restructuredtext en"

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import RelatedField, RelatedObject
from django.db.models.query import ValuesQuerySet
from utils import Utils
import django
import exceptions
import facade
import logging
import pr_time
import tagging.models
from pr_services.rpc.service import service_method

class ObjectManager(object):
    """Manage Power Reg persistent objects.

    Abstract base class for classes that manage persistent objects in the
    Power Reg 2 system.

    """
    def __init__(self):
        """ constructor """
        #: Dictionary of attribute names and the names of functions used to set them
        self.setters = {'notes' : 'set_many'}
        #: Dictionary of attribute names and the names of functions used to get them
        self.getters = {'id' : 'get_general',
            'notes' : 'get_many_to_many',
            'content_type' : 'get_content_type',
            'create_timestamp' : 'get_time',
            'save_timestamp' : 'get_time'}
        #: Sometimes we do nested iterations, such as going through a list of users, and
        #: for each one, figuring out which groups they belong to.  It's helpful to
        #: cache the relationship data here so don't have to fetch it again for each user.
        self.cache = {}
        #self.authorizer = facade.subsystems.Authorizer()
        self.logger = logging.getLogger(self.__module__)
        self.blame = None

    @property
    def authorizer(self):
        """Returns an instance of the latest Authorizer class

        Since the Authorizer class might get extended by a plugin we should
        avoid accessing by any other means than the facade itself.  However,
        since so much of our tests expect there to be an authorizer within
        their own class, this method will provide them backward compatibility.

        """
        return facade.subsystems.Authorizer()

    @service_method
    def update(self, auth_token, id, value_map):
        """
        Update a Power Reg persistent object
        
        :param id: Primary key for the object to update.
        :type id: int
        :param value_map: A map attributes to update and their new values.
                For a "many" end of a relationship, you may
                provide a list of foreign keys to be added, or
                you may provide a struct with two lists of keys
                indexed as 'add' and 'remove'.
        :type value_map: dict
        """

        pr_persistent_object = self._find_by_id(id)
        facade.subsystems.Setter(auth_token, self, pr_persistent_object, value_map)
        pr_persistent_object.save()

        return pr_persistent_object

    @service_method
    def delete(self, auth_token, pr_object_id):
        """
        Delete a Power Reg persistent object
        
        :param auth_token: The authentication token of the acting user
        :type auth_token: pr_services.models.AuthToken
        :param pr_object_id:  The primary key of the object to be deleted
        """

        object_to_be_deleted = self._find_by_id(pr_object_id)
        self.authorizer.check_delete_permissions(auth_token, object_to_be_deleted)
        object_to_be_deleted.delete()
        
    def _find_by_id(self, id, model_class=None):
        """
        Find a persistent object by primary key.
        
        :param id:  primary key of the object
        :param model_class:

               the model class of the object - None means to
               use the default Django model for this object manager class (which
               is specified in the self.my_django_model attribute)
        """
        
        if not model_class:
            return Utils.find_by_id(id, self.my_django_model)
        else:
            return Utils.find_by_id(id, model_class)

    @service_method
    def get_filtered(self, auth_token, filters, field_names=None):
        """
        Get Power Reg persistent objects filtered by various limits::

            Index values for filter structs:
            
              and                    Does a boolean and of a list of additional query dictionaries
              or                     Does a boolean or of a list of additional query dictionaries
              not                    Does a negation of a single query dictionary
              exact                  Exact match
              iexact                 Case-insensitive exact match
              greater_than           Greater Than
              less_than              Less Than
              greater_than_or_equal  Greater Than Or Equal
              less_than_or_equal     Less Than Or Equal
              begins                 Begins With
              ibegins                Case-insensitive begins with
              ends                   Ends With
              iends                  Case-insensitive ends with
              contains               Contains
              icontains              Case-insensitive contains
              range                  Within a range (pass beginning and ending points as an array)
              member                 Like SQL "IN", must be a member of the given list
        
        :param auth_token:
        :type auth_token: unicode
        :param filters:

                A struct of structs indexed by filter name. Each filter's
                struct should contain values indexed by field names.
        :type filters: dict
        :param field_names:

                Optional list of strings which specify the field names to return.
                Default is to return only the ids of the objects.  In fact, ids are
                always returned as long as the actor has permission to see them, so
                it is never necessary to ask for them, even though it also doesn't
                harm anything to ask (save a tiny bit of bandwidth).
        
        :type field_names: list
        """
        result = self.Filter(self)._filter_common(auth_token, filters, field_names)
        # Convert any instances of a ValuesQuerySet in the result dictionaries
        # into a normal Python list so it can be marshalled for RPC.
        for row in result:
            for key in row.keys():
                if isinstance(row[key], ValuesQuerySet):
                    row[key] = list(row[key])
        return result

    class Filter:
        """
        The Filter Class
        """

        def __init__(self, my_manager):
            """ constructor """

            self.my_manager = my_manager
            self.handlers = {
                'range' : self._handle_range,
            }
            
        operators = {
            'exact' : 'exact',
            'iexact' : 'iexact',
            'greater_than' : 'gt',
            'less_than' : 'lt',
            'greater_than_or_equal' : 'gte',
            'less_than_or_equal' : 'lte',
            'begins' : 'startswith',
            'ibegins' : 'istartswith',
            'ends' : 'endswith',
            'iends' : 'iendswith',
            'contains' : 'contains',
            'icontains' : 'icontains',
            'range' : 'range',
            'member' : 'in',
        }
        
        boolean_operators = ('and', 'or', 'not')
        
        tag_operators = ('tag_union', 'tag_intersection')

        def _handle_range(self, range_arg):
            """
            Handle_range
            
            This determines if a range is temporal, and if so, converts the endpoints from
            ISO8601 strings to python datetime objects
            
            :param range_arg: argument of the form [start, end] to give
                to the Django range filter operator
            """

            if len(range_arg) != 2 or type(range_arg[0]) != type(range_arg[1]):
                raise exceptions.RangeTakesTwoArgsException()

            if pr_time.is_iso8601(range_arg[0]) and pr_time.is_iso8601(range_arg[1]):
                ret = []
                for timestamp in range_arg:
                    ret.append(pr_time.iso8601_to_datetime(timestamp))
                return ret
            else:
                return range_arg

        def _filter_common(self, auth_token, filters, field_names=None):
            """
            Get objects filtered by various limits
            """
            
            if field_names is None:
                field_names = []
            
            query = self.construct_query(filters)
            query_set = self.my_manager.my_django_model.objects.filter(query)
            
            return facade.subsystems.Getter(auth_token, self.my_manager, query_set, field_names).results
        
        def validate_field_name_path(self, filter_dict, field_name_path):
            """
            Make sure that a path of field names is valid.  Raises an exception if not valid.
            
            :param filter_dict: the filter dictionary sent by the user (needed for exception handling)
            :type filter_dict: dict
            :param field_name_path: the field name path, made by splitting the field name around occurrences of '__'
            :type field_name_path: list
            """
            
            assert len(field_name_path) >= 2
            
            current_class = self.my_manager.my_django_model
            current_path = None
            for attribute_name in field_name_path[0:-1]:
                if not attribute_name:
                    raise exceptions.InvalidFilterException(filter_dict,
                        ('unrecognized attribute name [%s], path so far [%s]' %
                            (str(attribute_name), str(current_path))
                        ))
                if not current_path:
                    current_path = attribute_name
                else:
                    current_path += '__' + attribute_name
                    
                try:
                    related_field = current_class._meta.get_field_by_name(attribute_name)
                except FieldDoesNotExist:
                    raise
                if isinstance(related_field[0], RelatedField):
                    current_class = related_field[0].rel.to
                elif isinstance(related_field[0], RelatedObject):
                    current_class = related_field[0].model
                else:
                    raise exceptions.InvalidFilterException(filter_dict,
                        'unable to resolve related object reference %s' % current_path)
            
            try:
                last_field = current_class._meta.get_field_by_name(field_name_path[-1])
            except FieldDoesNotExist:
                raise exceptions.InvalidFilterException("unable to resolve field name [%s]" %
                    string.join(field_path, '__'))
        
        def construct_query(self, filter_dict):
            """
            construct a query based on a dictionary
            """
            ## handle boolean operators first, using recursion to apply them ##
            
            if ('and' in filter_dict) or ('or' in filter_dict) or ('not' in filter_dict):
                if len(filter_dict) != 1:
                    raise exceptions.InvalidFilterException(filter_dict,
                        'more than one top-level key with a boolean operator')
                operator = filter_dict.keys()[0]
                operand = filter_dict[operator]
                if (operator == 'and' or operator == 'or') and not \
                    (isinstance(operand, list) or isinstance(operand, tuple)):
                    
                    raise exceptions.InvalidFilterException(filter_dict,
                        'invalid operand -- expected a list or tuple')
                    
                if (operator == 'and' or operator == 'or') and len(operand) < 1:
                    raise exceptions.InvalidFilterException(filter_dict,
                        "invalid operand -- boolean 'and' and 'or' require an iterable with at least one element")
                    
                if operator == 'not' and not isinstance(operand, dict):
                    raise exceptions.InvalidFilterException(filter_dict,
                        'invalid operand -- expected a dictionary')
                
                if operator == 'and' or operator == 'or':
                    accumulated_query = self.construct_query(operand[0])
                    for additional_query in operand[1:]:
                        if operator == 'and':
                            accumulated_query = accumulated_query & self.construct_query(additional_query)
                        elif operator == 'or':
                            accumulated_query = accumulated_query | self.construct_query(additional_query)
                    return accumulated_query
                elif operator == 'not':
                    return ~(self.construct_query(operand))
                
            ## handle tag filters if present ##
            
            # make sure that we only have only one tag operator if we have any
            number_of_tag_operators = 0
            for op in filter_dict:
                if op in self.tag_operators:
                    number_of_tag_operators += 1
            if number_of_tag_operators > 1:
                raise exceptions.InvalidFilterException(
                    'no more than one tag operator is allowed')
                
            if number_of_tag_operators == 1:
                if len(filter_dict) > 1:
                    raise exceptions.InvalidFilterException(
                        'No other filters are allowed with a tag operation.  You should' +\
                        ' probably use Boolean expressions.')
                tag_union_operand = None
                tag_intersection_operand = None
                if 'tag_union' in filter_dict:
                    tag_union_operand = filter_dict['tag_union']
                elif 'tag_intersection' in filter_dict:
                    tag_intersection_operand = filter_dict['tag_intersection']
                if tag_union_operand is not None:
                    query_set = tagging.models.TaggedItem.objects.get_union_by_model(
                        self.my_manager.my_django_model,
                        tag_union_operand)
                elif tag_intersection_operand is not None:
                    query_set = tagging.models.TaggedItem.objects.get_by_model(
                        self.my_manager.my_django_model,
                        tag_intersection_operand)
                pk_list = list()
                for obj in query_set:
                    pk_list.append(obj.id)
                return Q(id__in=pk_list)
                    
            # recursion base case -- no boolean operator present in top-level of operators
            
            #: Dictionary of filter arguments that will be passed to django.
            #: for example, {'start__gte' : '2008-06-12', 'end__lte' : '2008-06-13'} would
            #: be used to construct a filter call like this:
            #:    <your_model>.objects.filter(start__gte = '2008-06-12', end__lte = '2008-06-13')
            #:
            #: See django's database API docs on filtering for the specifics.
            django_filter_arguments = {}
            for operator in filter_dict:
                if (operator in self.operators) and isinstance(filter_dict[operator], dict):
                # If we support this filter operator and have at least one value on which to filter...
                    # For each field name on which we are filtering...
                    for field_name in filter_dict[operator].keys():
                        if field_name.find('__') != -1:
                            field_name_path = field_name.split('__')
                            self.validate_field_name_path(filter_dict, field_name_path)
                            
                        new_arg = filter_dict[operator][field_name] # We will mangle this.

                        # If we have a special handler for this operator, apply it.
                        if operator in self.handlers:
                            new_arg = self.handlers[operator](new_arg)

                        # construct the name of the argument to pass to django's filter method
                        # (e.g. 'id__exact')
                        django_filter_arg_name = str(field_name) + '__' + str(self.operators[operator])
                        
                        # construct a dictionary mapping names of arguments to pass to the
                        # django filter method with their values, like {'id__exact':'1'}.
                        # See comments a few lines above after the definition of the
                        # local django_filter_arguments variable for more details.
                        django_filter_arguments[django_filter_arg_name] = new_arg
                else:
                    # We weren't given a valid operator.
                    raise exceptions.InvalidFilterOperatorException(operator)

            # the ** operator expands a dictionary to a series of named arguments
            query = Q(**django_filter_arguments)
            return query

    def _get_blame(self, auth_token):
        """
        looks for a cached blame and returns it if one exists. If not, returns
        a new blame (but does not cache the new one!). Service methods that
        wish to cache a blame are responsible for removing it at the end of
        the call.
        """

        if self.blame is None:
            return facade.managers.BlameManager().create(auth_token)
        else:
            return self.blame
    

# vim:tabstop=5 shiftwidth=4 expandtab
