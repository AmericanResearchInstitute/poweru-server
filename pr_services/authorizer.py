"""
This module contains the authorizer class, which is able
to answer the question of whether or not a particular
user has access to a particular attribute on a particular
model.
"""

from __future__ import with_statement
import copy
import cPickle
from datetime import datetime, timedelta
import threading
from django.core.exceptions import ObjectDoesNotExist
from authorizer_decorators import *
import exceptions
import facade
import pr_models
import logging
from utils import Utils

class Authorizer(object):
    # Store a single instance of an Authorizer object, so we can manage the ACL cache effectively
    singleton_instance = None
    persistent_cache = None
    persistent_cache_lock = threading.RLock()

    def __init__(self):
        """
        The authorizer initialization gets a lock on the persistent_cache,
        which is a place to store ACL definitions. If empty or stale, it will
        be populated.
        """

        self.logger = facade.subsystems.Logger('pr_services.authorizer', logging.getLevelName('TRACE'))

        with self.__class__.persistent_cache_lock:
            if self.__class__.persistent_cache is None:
                self.__class__._load_acls()
            self.cache = copy.deepcopy(self.__class__.persistent_cache)

    @classmethod
    def __new__(cls, *args, **kwargs):
        # Check to see if a __single exists already for this class
        # Compare class types instead of just looking for None so
        # that subclasses will create their own __single objects
        if cls.singleton_instance is None or cls != type(cls.singleton_instance):
            cls.singleton_instance = object.__new__(cls)
        return cls.singleton_instance

    @classmethod
    def _load_acls(cls):
        """
        Load the ACLs from the database and stick them in the persistent_cache
        for all instances (in this interpreter anyway) to share. 
        """
        with cls.persistent_cache_lock:
            cls.persistent_cache = {}
            all_acls = facade.models.ACL.objects.select_related().all()
            cls.persistent_cache['acls'] = []
            for an_acl in all_acls:
                cached_acl = {}
                cached_acl['acl_object'] = an_acl
                cached_acl['ac_method_calls'] = []
                for a_method_call in an_acl.ac_method_calls.select_related().all():
                    cached_call = {}
                    cached_call['method_to_run'] = a_method_call.ac_check_method.name
                    pickled_parameters_str = str(a_method_call.ac_check_parameters)
                    if pickled_parameters_str:
                        cached_call['parameters'] = cPickle.loads(pickled_parameters_str)
                    copied_ac_method_call = cached_call.copy()
                    copied_ac_method_call['check_passed'] = {}
                    cached_acl['ac_method_calls'].append(copied_ac_method_call)
                acl_str = str(an_acl.acl)
                if acl_str:
                    cached_acl['acl'] = cPickle.loads(str(an_acl.acl))
                else:
                    cached_acl['acl'] = {}
                if an_acl.arbitrary_perm_list:
                    cached_acl['arbitrary_perm_list'] = cPickle.loads(str(an_acl.arbitrary_perm_list))
                cls.persistent_cache['acls'].append(cached_acl.copy())
            cls.persistent_cache['timestamp'] = datetime.now()
        # Notify all the instances of the Authorizer class that we have a new cache for them to copy
        if cls.singleton_instance is not None:
            cls.singleton_instance.__init__()

    def check_arbitrary_permissions(self, auth_token, requested_permission):
        """
        This method checks the arbitrary permission list to see
        if the user has the requested access.  If they do not, it
        raises an exception.  If they do, it returns silently.
        
        @param requested_permission    A string of the permission
                that should be checked for.  If it is not granted
                by one of the ACLs that the user is determined to
                be acting within, the method raises an exception.
        """
        acls_to_check = self._get_relevant_acls_for_arbitrary_permissions(
            requested_permission)
        for acl in acls_to_check:
            if self._acl_checks_pass(auth_token, None, acl):
                arb_perms_granted = acl['arbitrary_perm_list']
                if requested_permission in arb_perms_granted:
                    return
        raise exceptions.PermissionDeniedException()

    def check_create_permissions(self, auth_token, actee):
        """
        This method checks whether or not the actor has the create permissions
        being requested, and raises an exception if they do not.
        
        @param actee  The object being created (you will need to instantiate it
                before calling this method)
        """
        actee_type = actee._meta.object_name # We need to use introspection to get the type of the actee
        namespace = actee._meta.app_label
        acls_to_check = self._get_relevant_acls_for_cd(actee_type, namespace, 'c')
        permission_granted = False
        # For each of the ACLs, we need to run their ACCheckMethods, and if they
        # all pass for that ACL, we add the ACL's permissions to actors_acls
        for acl in acls_to_check:
            # If all the checks have passed, we need to grant permissions to the user from the ACL 
            acl_checks_passed = self._acl_checks_pass(auth_token, actee, acl)
            self.logger.commit()
            if acl_checks_passed:
                try:
                    permission_granted = acl['acl'][actee_type]['c']
                except KeyError, e:
                    if e.args and e.args[0] == actee_type:
                        actee_type = '%s.%s' % (namespace, actee_type)
                        permission_granted = acl['acl'][actee_type]['c']
                    else:
                        raise
                if permission_granted:
                    return
        if not permission_granted:
            raise exceptions.PermissionDeniedException()
        
    def check_read_permissions(self, auth_token, actee, requested_attributes):
        """
        This method checks permissions on a user when we know what fields
        they are requesting.  It will always raise a permission denied
        exception if the user doesn't have access to a particular attribute
        they are requesting.  If you just want to know what fields they have
        access to you should use the get_authorized_attributes method and
        not this method.
        
        @param actee                The object being acted upon
        @param requested_attributes The list of fields that the user is attempting to read
        """
        authorized_attributes = self.get_authorized_attributes(auth_token, actee,
            requested_attributes, 'r')
        for field in requested_attributes:
            if field not in authorized_attributes:
                # We need to use introspection to get the type of the actee
                actee_type = actee._meta.object_name
                raise exceptions.PermissionDeniedException(field, actee_type)

    def check_update_permissions(self, auth_token, actee, update_parameters):
        """
        This method checks permissions on a user when we know what fields
        they are requesting.  It will always raise a permission denied
        exception if the user doesn't have access to a particular attribute
        they are requesting.  If you just want to know what fields they have
        access to you should use the get_authorized_attributes method and
        not this method.
        
        @param actee                The object being acted upon
        @param update_parameters    The dictionary of fields that the user is attempting to update and the values they are trying to update them to
        """
        authorized_attributes = self.get_authorized_attributes(auth_token, actee,
            update_parameters.keys(), 'u', update_parameters)
        for field in update_parameters.keys():
            if field not in authorized_attributes:
                # We need to use introspection to get the type of the actee
                actee_type = actee._meta.object_name
                raise exceptions.PermissionDeniedException(field, actee_type)

    def check_delete_permissions(self, auth_token, actee):
        """
        This method checks whether or not the actor has the delete permissions
        being requested, and raises an exception if they do not.
        
        @param actee  The object the actor wishes to delete
        """
        actee_type = actee._meta.object_name # We need to use introspection to get the type of the actee
        namespace = actee._meta.app_label
        acls_to_check = self._get_relevant_acls_for_cd(actee_type, namespace, 'd')
        permission_granted = False
        # For each of the ACLs, we need to run their ac_check_methods, and if they all pass
        # for that ACL, we add the ACL's permissions to actors_acls
        for acl in acls_to_check:
            # If all the checks have passed, we need to grant permissions to the user from the
            # ACL 
            if self._acl_checks_pass(auth_token, actee, acl):
                permission_granted = acl['acl'][actee_type]['d']
                if permission_granted:
                    return
        if not permission_granted:
            raise exceptions.PermissionDeniedException()

    def get_authorized_attributes(self, auth_token, actee, requested_fields, access_type,
        update_dict=None):
        
        """
        This method returns a list of fields for which the actor has read permissions for on the actee.
        
        @param actee            The object being acted upon
        @param requested_fields A list of the fields that the user would like to read
        @type requested_fields  list of string
        @param access_type      The type of access being requested.  Either 'r' (read) or 'u' (update)
        @type access_type       string
        @param update_dict      This optional parameter should be used when asking about
                                authorized attributes to update, and should be the dict of
                                parameters to be updated on the object
        @type update_dict       dict
        @return                 A list of fields that the user is authorized to access.  This
                                method can also raise a PermissionDeniedException.
        """
        
        if update_dict is None:
            update_dict = {}
        # We need to use introspection to get the type of the actee
        actee_type = actee._meta.object_name 
        namespace = actee._meta.app_label
        acls_to_check = self._get_relevant_acls_for_attributes(actee_type, namespace, requested_fields,
            access_type)
        authorized_attributes = [] # The authorized attributes that we are granting to the actor
        # For each of the ACLs, we need to run their ac_check_methods, and if they all pass for
        # that ACL, we add the ACLs attributes to actors_acls
        for potential_acl_dict in acls_to_check:
            # If all the checks have passed, we need to grant permissions to the user from the ACL 
            checks_pass = self._acl_checks_pass(auth_token, actee, potential_acl_dict, update_dict)
            self.logger.commit()
            if checks_pass:
                attributes_granted = potential_acl_dict['acl'][actee_type][access_type]
                all_requested_fields_granted = True
                # If the user has requested fields, we can perform some optimizations
                if len(requested_fields) != 0: 
                    for requested_field in requested_fields:
                        # If the requested field has been granted, add it to authorized_attributes
                        if requested_field in attributes_granted:
                            authorized_attributes.append(requested_field)
                        # If the field hasn't been granted now, and not in the past, then not all
                        # fields have been granted and we need to keep checking
                        elif requested_field not in authorized_attributes: 
                            all_requested_fields_granted = False
                    # If all the requested fields are granted then we can stop checking and save
                    # the world now
                    if all_requested_fields_granted:
                        break
                else: # Else, we just append the new fields to authorized attributes
                    for acquired_field in attributes_granted:
                        if acquired_field not in authorized_attributes:
                            authorized_attributes.append(acquired_field)
        return authorized_attributes

    def _get_relevant_acls_for_cd(self, actee_type, namespace, access_type):
        """
        This method returns a list of relevant system ACLs to be used
        in our authorization check for create 'c' or delete 'd' calls.  ACLs that do not deal with the requested
        access for the object type will not be returned to save time.

        @param actee_type   The type of the object that the actor is attempting
                            to act upon
        @param namespace    generally the name of the application from which the model comes.
                            The actee_type will first be searched for in the global name space,
                            and if not found, then in this namespace.
        @param access_type  Indicates whether the user would like to create ('c') or delete ('d')
        @type access_type   string
        @return             A list of ACLs that should be used to check whether
                            access is allowed or not
        """
        # We can use the method already written under another name for this, which allows us to use this more nicely named wrapper
        return self._get_relevant_acls_for_attributes(actee_type, namespace, [], access_type)

    def _get_relevant_acls_for_attributes(self, actee_type, namespace, requested_fields, access_type):
        """
        This method returns a list of relevant system ACLs to be used
        in our authorization check.  ACLs that do not deal with the requested
        access for the object type will not be returned to save time.
        
        @param actee_type       The type of the object that the actor is attempting
                                to act upon
        @param namespace        generally the name of the application from which the model comes.
                                The actee_type will first be searched for in the global name space,
                                and if not found, then in this namespace.
        @param requested_fields A list of strings of the names of the fields being requested.  If this list is empty, the method will just return
                                all the ACLs that have the actee_type in their acl attribute (assuming that the user wants all possible attributes)
        @type requested_fields  list
        @param access_type      Indicates whether the user would like to read ('r'), update ('u'), create ('c'), or delete ('d')
        @type access_type       string
        @return                 A list of ACLs that should be used to check whether
                                access is allowed or not
        """

        relevant_acls = []
        for potential_acl_dict in self.cache['acls']:
            acl = potential_acl_dict['acl']
            # If the type of the actee isn't in the acl, then it isn't relevant and we won't use it
            if actee_type not in acl:
                actee_name = '%s.%s' % (namespace, actee_type)
            else:
                actee_name = actee_type
            if actee_name in acl:
                # If the user is requesting create or delete, there will not be any requested fields and the access type will be 'c' or 'd'
                if len(requested_fields) == 0 and access_type in ['c', 'd']:
                    # If this ACL grants the permission, add it to the potential ACL list
                    if acl[actee_name][access_type]:
                        relevant_acls.append(potential_acl_dict)
                    continue
                # Check the list of potential fields against the requested.  If any
                # of the requested fields are in the potential, append the ACL
                potential_fields = acl[actee_name][access_type]
                for requested_field in requested_fields:
                    if requested_field in potential_fields:
                        relevant_acls.append(potential_acl_dict)
                        break
        return relevant_acls

    def _get_relevant_acls_for_arbitrary_permissions(self, requested_permission):
        """
        This method determines which ACLs we might possibly consider when
        testing for arbitrary permissions.  It will return a list of the relevant
        ACLs.
        
        @param requested_permission   A string of the requested arbitrary permission
        @return                       A list of ACLs that should be used to check whether
                access is allowed or not
        """
        relevant_acls = []
        for potential_acl in self.cache['acls']:
            if 'arbitrary_perm_list' in potential_acl:
                arbitrary_perm_list = potential_acl['arbitrary_perm_list']
            else:
                continue
            if requested_permission in arbitrary_perm_list:
                relevant_acls.append(potential_acl)
        return relevant_acls

    def _acl_checks_pass(self, auth_token, actee, acl_dict, update_dict=None):
        """
        This method performs the tests found in the ACL and returns True
        only if the result of all the tests ANDed together is True
        
        @param actee        The object that the acting user is acting upon
        @param acl_dict     The ACL that we are running checks using, to determine
                            whether the user is acting under the ACL or not
        @type acl_dict      dict
        @param update_dict  A dictionary of the fields and the values that they are being updated to for the actee.  Optional (meant
                            only to be used in an update call).
        @type update_dict   dict
        @return             Boolean value indicating True if the user is acting
                            under the ACL, or False otherwise
        @rtype bool
        """
        if not isinstance(auth_token, facade.models.AuthToken):
            if not (auth_token is None or auth_token == ''):
                raise exceptions.NotLoggedInException
            cache_key = ''
        else:
            cache_key = auth_token.session_id
        
        if update_dict is None:
            update_dict = {}

        #: the number of membership tests passed so far
        num_passed_checks = 0
        #: the number of membership tests that must be passed for
        #: membership in the given ACL in the context of the given actee
        num_checks_need_to_pass = len(acl_dict['ac_method_calls'])
        for ac_method_call_dict in acl_dict['ac_method_calls']:
            log_entry = [acl_dict['acl_object'].role.name, ac_method_call_dict['method_to_run']]
            if self.logger:
                self.logger.add_row(log_entry)
            # Get the method to be run
            method_to_run = getattr(self, ac_method_call_dict['method_to_run'])
            # If the check_method isn't for guests, and the actor is a guest, we should
            # go ahead and return False
            if not hasattr(method_to_run, 'allow_guests') and self.actor_is_guest(auth_token):
                log_entry.append(False)
                return False
            # Get the dictionary of parameters to be passed to the check method, and
            # add the actor and actee to the mix
            method_parameters = {}
            if 'parameters' in ac_method_call_dict:
                method_parameters = ac_method_call_dict['parameters']
            method_parameters['actee'] = actee
            method_parameters['auth_token'] = auth_token
            if hasattr(method_to_run, 'uses_update_dict') and getattr(method_to_run, 'uses_update_dict'):
                if len(update_dict) != 0:
                    method_parameters['update_dict'] = update_dict
                else:
                    # The user isn't trying to update anything, let's decrement the number of checks that need to pass
                    num_checks_need_to_pass -= 1
                    continue
            # If any method fails, we return False since we require them to all pass (AND operation) 
            try:
                # If the test does not refer to the actee in any way, we
                # can cache its result to use later.
                if hasattr(method_to_run, 'does_not_use_actee') and method_to_run.does_not_use_actee:
                    # If we have a cached value for the test, use it.
                    try:
                        method_passed = ac_method_call_dict['check_passed'][cache_key]
                    except KeyError:
                        # cache miss:
                        # We don't have a cached value -- compute one and cache it.
                        method_passed = method_to_run(**method_parameters)
                        ac_method_call_dict['check_passed'][cache_key] = method_passed
                else:
                    # We can't cache the result of this membership test, since it
                    # relies on the actee.  Run the method.
                    method_passed = method_to_run(**method_parameters)
                log_entry.append(method_passed)
                if method_passed:
                    num_passed_checks += 1
                else:
                    return False
            except exceptions.InvalidActeeTypeException:
                log_entry.append('Invalid Actee Type')
                # Ignore membership tests that don't apply to this actee.
                num_checks_need_to_pass -= 1
                continue
            except exceptions.AttributeNotUpdatedException:
                # Ignore checks that look for an update that isn't happening
                num_checks_need_to_pass -= 1
                continue
        # Return true if
        #   (a) We don't have only membership tests that are not applicable (due to
        #       the exceptions.InvalidActeeTypeException's having been thrown).
        #   (b) We have passed all of the applicable membership tests.
        # Otherwise, return false.
        if num_passed_checks > 0 and num_passed_checks == num_checks_need_to_pass:
            return True
        return False

    #################################################################
    #
    # Below this block are where the methods that we use for the
    # authorization checks are found.  These methods are available to
    # be used through the ACL manager to define ACLs, and each one
    # must take an actor object and an actee object as its first
    # two parameters.
    #
    #################################################################

    #################################################################
    #
    # Methods for which actee is any PRModel.
    #
    #################################################################
    def actor_owns_prmodel(self, auth_token, actee):
        """
        Returns True if the actor is the same User object as is listed in the PRModel's owner field, or if the PRModel has None in its owner field.
        """
        if not isinstance(actee, pr_models.OwnedPRModel):
            raise exceptions.InvalidActeeTypeException()
        try:
            if actee.owner is None:
                return True
            elif auth_token.user.id == actee.owner.id:
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################
    #
    # Methods for which actee is an address.
    #
    #################################################################
    def actor_owns_address(self, auth_token, actee):
        """
        Returns True if the address object is either the user's
        shipping or billing address, False otherwise.
        
        @param actee  The address object in question
        """

        if not isinstance(actee, facade.models.Address):
            raise exceptions.InvalidActeeTypeException()
        if auth_token.user.billing_address and auth_token.user.billing_address.id == actee.id:
            return True
        if auth_token.user.shipping_address and auth_token.user.shipping_address.id == actee.id:
            return True
        return False

    #################################################################################
    #
    # Methods for which actee is an Assignment
    #
    #################################################################################
    def actor_has_completed_assignment_prerequisites(self, auth_token, actee):
        """
        Returns True iff the actor has completed all of the prerequisite tasks for the task being queried.
        """
        if not isinstance(actee, facade.models.Assignment):
            raise exceptions.InvalidActeeTypeException()
        try:
            if self.actor_has_completed_task_prerequisites(auth_token, actee.task):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    def actor_owns_assignment(self, auth_token, actee):
        """
        Returns True iff the actor is the owner of the Assignment
        """

        if not isinstance(actee, facade.models.Assignment):
            raise exceptions.InvalidActeeTypeException()
        try:
            if auth_token.user.id == actee.user.id:
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    @allow_guests
    def actor_owns_assignment_or_is_guest(self, auth_token, actee):
        """
        Returns True if the actor is the owner of the Assignment, or if the actor is a guest and the Assignment doesn't have a user defined.
        """
        if not isinstance(actee, facade.models.Assignment):
            raise exceptions.InvalidActeeTypeException()
        try:
            if actee.user is None and not isinstance(auth_token, facade.models.AuthToken):
                return True
            else:
                return self.actor_owns_assignment(auth_token, actee)
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    def assignment_prerequisites_met(self, auth_token, actee):
        """
        Returns True iff the assignment's prerequisites have been met
        """

        if not isinstance(actee, facade.models.Assignment):
            raise exceptions.InvalidActeeTypeException()
        return actee.prerequisites_met

    #################################################################################
    #
    # Methods for which actee is an AssignmentAttempt
    #
    #################################################################################

    def assignment_venue_matches_actor_preferred_venue(self, auth_token, actee):
        """
        Returns true if the assignment is at a venue that matches the actor's
        preferred venue

        @param actee      Instance of Assignment
        """
        
        if not isinstance(actee, facade.models.Assignment):
            raise exceptions.InvalidActeeTypeException()

        surr = actee.task.downcast_completely()

        if not isinstance(surr, facade.models.SessionUserRoleRequirement):
            raise exceptions.InvalidActeeTypeException()

        try:
            actor_venues = set(auth_token.user.preferred_venues.values_list('id', flat = True))

            try:
                if surr.session.room.venue.id in actor_venues:
                    return True
            except ObjectDoesNotExist:
                pass
            except AttributeError:
                pass

            try:
                if surr.session.event.venue.id in actor_venues:
                    return True
            except ObjectDoesNotExist:
                pass
            except AttributeError:
                pass

        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    def actor_owns_assignment_attempt(self, auth_token, actee):
        """
        Returns True iff the actor is the owner of the Assignment
        """

        if not isinstance(actee, facade.models.AssignmentAttempt):
            raise exceptions.InvalidActeeTypeException()

        return self.actor_owns_assignment(auth_token, actee.assignment)

    def assignment_attempt_prerequisites_met(self, auth_token, actee):
        """
        Returns True iff the assignment_attempt's prerequisites have been met
        """

        if not isinstance(actee, facade.models.AssignmentAttempt):
            raise exceptions.InvalidActeeTypeException()

        return self.assignment_prerequisites_met(auth_token, actee.assignment)

    def assignment_attempt_meets_date_restrictions(self, auth_token, actee):
        """
        Returns True iff the assignment_attempt's dates meet the restrictions
        defined on the Assignment
        """

        if not isinstance(actee, facade.models.AssignmentAttempt):
            raise exceptions.InvalidActeeTypeException()

        if isinstance(actee.date_started, datetime) and isinstance(actee.assignment.effective_date_assigned, datetime) and actee.date_started < actee.assignment.effective_date_assigned:
            return False

        return True

    #################################################################################
    #
    # Methods for which actee is a credential
    #
    #################################################################################
    def actor_owns_credential(self, auth_token, actee):
        """
        Returns True iff the actor is the owner of the Credential
        """
        if not isinstance(actee, facade.models.Credential):
            raise exceptions.InvalidActeeTypeException()
        try:
            if auth_token.user.id == actee.user.id:
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################
    #
    # Methods for which actee is a DomainAffiliation
    #
    #################################################################
    def actor_related_to_domain_affiliation(self, auth_token, actee):
        """
        Returns True if the DomainAffiliation's 'user' attribute
        references the actor
        
        @param actee  The DomainAffiliation object in question
        """

        if not isinstance(actee, facade.models.DomainAffiliation):
            raise exceptions.InvalidActeeTypeException()

        return bool(auth_token.user.id == actee.user.id)

    #################################################################################
    #
    # Methods for which actee is an event
    #
    #################################################################################

    def actor_owns_event(self, auth_token, actee):
        """
        Returns true if the actor is the owner of an event.
        """
        if not isinstance(actee, facade.models.Event):
            raise exceptions.InvalidActeeTypeException()

        try:
            if auth_token.user.id == actee.owner.id:
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False
    

    #################################################################################
    #
    # Methods for which actee is an ExamSession
    #
    #################################################################################
    def populated_exam_session_is_finished(self, auth_token, actee):
        """
        Does nothing if the ExamSession does not have any answered questions
        or ratings.  That allows us to use the same ACL to allow creation of
        an ExamSession and allow reading results.  Returns True if the
        ExamSession has been finished, else False.
        
        @param actee      Instance of ExamSession
        """
        # This test allows us to know if this ExamSession is new or not by virtue of it being populated.
        if not (isinstance(actee, facade.models.ExamSession) and (
                actee.response_questions.count())):
            raise exceptions.InvalidActeeTypeException()
        return bool(actee.date_completed)

    #################################################################################
    #
    # Methods for which actee is a refund
    #
    #################################################################################

    def refund_does_not_exceed_payment(self, auth_token, actee):
        """
        Returns true if the refund does not put the total amount of
        refunds for a particular payment over the value of the payment.
        
        @param actee      Instance of refund
        """

        if not isinstance(actee, facade.models.Refund):
            raise exceptions.InvalidActeeTypeException()
        total_refunds = 0
        for r in actee.payment.refunds.values_list('amount', flat = True):
            total_refunds += r
        if actee.amount > actee.payment.amount - total_refunds:
            return False
        else:
            return True

    #################################################################################
    #
    # Methods for which actee is a session
    #
    #################################################################################

    def actor_owns_session(self, auth_token, actee):
        """
        Returns True if the actor owns the event associated with this session.
        """
        if not isinstance(actee, facade.models.Session):
            raise exceptions.InvalidActeeTypeException()

        try:
            the_event = actee.event
            if self.actor_owns_event(auth_token, the_event):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    def actor_is_product_line_manager_of_session(self, auth_token, actee):
        """
        Returns true if the actor is a product line manager for the given session.
        
        @param actee      Instance of session
        """
        if not isinstance(actee, facade.models.Session):
            raise exceptions.InvalidActeeTypeException()
            
        try:
            if auth_token.user.id in actee.product_line.managers.values_list('id', flat=True):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass

        # Now see if this session's session_template has the actor as a PLM
        try:
            if auth_token.user.id in actee.session_template.product_line.managers.values_list('id', flat = True):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################################
    #
    # Methods for which actee is a session_template
    #
    #################################################################################

    def actor_is_product_line_manager_of_session_template(self, auth_token, actee):
        """
        Returns true if the actor is a product line manager for the given session_template
        
        @param actee      Instance of session_template
        """

        if not isinstance(actee, facade.models.SessionTemplate):
            raise exceptions.InvalidActeeTypeException()
        try:
            if auth_token.user.id in actee.product_line.managers.values_list('id',
                    flat = True):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################################
    #
    # Methods for which actee is a session_user_role_requirement
    #
    #################################################################################

    @allow_guests
    def surr_is_of_a_particular_sur(self, auth_token, actee, session_user_role_id):
        """
        Returns True iff the session_user_role associate with the actee is the same as the
        session_user_role specified by the parameter session_user_role.
        """
        if not isinstance(actee, facade.models.SessionUserRoleRequirement):
            raise exceptions.InvalidActeeTypeException()
        try:
            if int(actee.session_user_role.id) == int(session_user_role_id):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    def actor_owns_session_user_role_requirement(self, auth_token, actee):
        """
        Returns True if the session associated with the session_user_role_requirement is owned
        by the actor
        """
        
        if not isinstance(actee, facade.models.SessionUserRoleRequirement):
            raise exceptions.InvalidActeeTypeException()

        try:
            the_session = actee.session
            if self.actor_owns_session(auth_token, the_session):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################################
    #
    # Methods for which actee is a group
    #
    #################################################################################

    def actor_is_group_manager(self, auth_token, actee):
        """
        Returns True if the actor is the manager of the group.
        
        @param actee  Instance of a group
        """

        if not isinstance(actee, facade.models.Group):
            raise exceptions.InvalidActeeTypeException()
        try:
            if auth_token.user.id in actee.managers.values_list('id', flat=True):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False
    
    def actor_is_in_actee_which_is_a_group(self, auth_token, actee):
        """Returns true if the actee is a group and the actor is a member thereof."""

        if not isinstance(actee, facade.models.Group):
            raise exceptions.InvalidActeeTypeException()
        try:
            if auth_token.user.id in actee.users.values_list('id', flat=True):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False
        

    #################################################################################
    #
    # Methods for which actee is an organization 
    #
    #################################################################################
    
    def actor_is_in_actee_which_is_an_organization(self, auth_token, actee):
        """
        Returns True if the actee is an Organization and the actor belongs to that
        organization.
        """
        
        if not isinstance(actee, facade.models.Organization):
            raise exceptions.InvalidActeeTypeException()
        if not isinstance(auth_token, facade.models.AuthToken):
            return False 
        if actee.id in (x.id for x in auth_token.user.organizations):
            return True
        return False

    #################################################################################
    #
    # Methods for which actee is a payment
    #
    #################################################################################

    def actor_owns_payment(self, auth_token, actee):
        """
        Returns true if the actor owns the payment.
        
        @param actee      Instance of a purchase_order
        """

        if not isinstance(actee, facade.models.Payment):
            raise exceptions.InvalidActeeTypeException()
            
        try:
            if auth_token.user.id == actee.purchase_order.user.id:
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################################
    #
    # Methods for which actee is a product_line
    #
    #################################################################################

    def actor_is_product_line_manager_of_product_line(self, auth_token, actee):
        """
        Returns true if the actor is a product line manager for the given product line.
        
        @param actee      Instance of product_line
        """

        if not isinstance(actee, facade.models.ProductLine):
            raise exceptions.InvalidActeeTypeException()
            
        if auth_token.user.id in actee.managers.values_list('id', flat = True):
            return True
        else:
            return False

    #################################################################################
    #
    # Methods for which actee is a purchase_order
    #
    #################################################################################

    def purchase_order_has_payments(self, auth_token, actee):
        """
        Returns true if the purchase order being accessed has at least one payment.
        
        @param actee      Instance of a purchase_order
        """

        if not isinstance(actee, facade.models.PurchaseOrder):
            raise exceptions.InvalidActeeTypeException()

        return True if actee.payments.count() else False

    def purchase_order_has_no_payments(self, auth_token, actee):
        """
        Returns true if the purchase order being accessed has no payments.
        
        @param actee      Instance of a purchase_order
        """

        if not isinstance(actee, facade.models.PurchaseOrder):
            raise exceptions.InvalidActeeTypeException()

        return False if actee.payments.count() else True

    def actor_owns_purchase_order(self, auth_token, actee):
        """
        Returns true if the actor owns the purchase order being accessed.
        
        @param actee      Instance of a purchase_order
        """

        if not isinstance(actee, facade.models.PurchaseOrder):
            raise exceptions.InvalidActeeTypeException()
            
        try:
            if auth_token.user.id == actee.user.id:
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################################
    #
    # Methods for which actee is a QuestionResponse
    #
    #################################################################################
    def actor_owns_question_response(self, auth_token, actee):
        """
        Returns True iff the QuestionResponse is for an ExamSession owned by the actor.
        """
        if not isinstance(actee, facade.models.Response):
            raise exceptions.InvalidActeeTypeException()
        try:
            return self.actor_owns_assignment(auth_token, actee.exam_session)
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################################
    #
    # Methods for which actee is a Task
    #
    #################################################################################
    def actor_has_completed_task_prerequisites(self, auth_token, actee):
        """
        Returns True iff the actor has completed all of the prerequisite tasks for the task being queried.
        """
        if not isinstance(actee, facade.models.Task):
            raise exceptions.InvalidActeeTypeException()
        try:
            if actee.prerequisites_met(auth_token.user):
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################################
    #
    # Methods for which actee is a training_unit_authorization
    #
    #################################################################################

    def actor_owns_training_unit_authorization(self, auth_token, actee):
        """
        Returns true if the actor owns the purchase order being accessed.
        
        @param actee      Instance of a purchase_order
        """

        if not isinstance(actee, facade.models.TrainingUnitAuthorization):
            raise exceptions.InvalidActeeTypeException()
            
        try:
            if auth_token.user.id == actee.user.id:
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################################
    #
    # Methods for which actee is a User
    #
    #################################################################################
    
    def actee_is_in_group_and_domain(self, auth_token, actee, group_id, domain_id):
        """
        If the actee is in the group, the method returns True iff they are also of the domain.
        If they are not in the group, it will return False.
        
        This is useful for making sure that participants who register themselves are
        in a particular domain, such as 'constantcontact.com' for the Constant Contact variant.
        
        Note that returning False instead of True if the user is not a part of
        the specified group is a different behavior from what the Constant
        Contact variant does!

        @param actee    The user object in question
        @type actee     user
        @param group_id The primary key of the group that the actee must be a member of
        @param domain_id the primary key of the domain
        """
        
        if not isinstance(actee, facade.models.User):
            raise exceptions.InvalidActeeTypeException()
        
        if group_id in actee.groups.all().values_list('id', flat=True):
            if actee.domain_affiliations.filter(domain__id=domain_id).count() == 0:
                return False # The user is in the group, but not the domain
            else:
                return True # The user is in the group and the domain, so let's allow
            
        return False

    @uses_update_dict
    def actor_is_adding_allowed_many_ended_objects_to_user(self, auth_token, actee, attribute_name, allowed_pks, update_dict):
        """
        This is a strange new breed of auth_check that concerns itself with the update_dict.  It ensures that the update_dict is only
        attempting to add items from the list of allowed primary keys to the attribute on the actee.  It will return false if any
        'remove' operation is in the dict, or if any primary key appears in the add list that is not in the allowed primary key list.

        @param auth_token       The authentication token of the acting user
        @type auth_token        auth_token
        @param actee            A user object that we are evaluation authorization for
        @type actee             user
        @param attribute_name   The attribute that we are authorizing the update call based on
        @type attribute_name    string
        @param allowed_pks      A list of primary keys that we will allow the actor to add to the actee's many ended attribute
        @type allowed_pks       list
        @param update_dict      The dictionary of changes that the actor is attempting to apply
                                to actee
        @type update_dict       dict
        @return                 A boolean of whether or not the actor will be allowed to run
                                the update call
        @raises                 InvalidActeeTypeException, AttributeNotInUpdateDictException
        """
        if not isinstance(actee, facade.models.User):
            raise exceptions.InvalidActeeTypeException()
        if attribute_name not in update_dict:
            raise exceptions.AttributeNotUpdatedException()
        current_pks = []
        for current_foreign_object in getattr(actee, attribute_name).all():
            current_pks.append(current_foreign_object.id)
        added_keys = update_dict[attribute_name]
        if isinstance(added_keys, dict):
            # For now we will hate on the user if they try to remove an item.  We can change this later if we need to, but for now
            # this meets our needs.
            if 'remove' in added_keys:
                return False
            added_keys = added_keys['add']
        for key in added_keys:
            if key not in current_pks and key not in allowed_pks:
                # The user is attempting to add a key that the actee doesn't already have and it isn't in the allowed list
                return False
        # There weren't any objections, so I guess we are clear
        return True

    def actor_actee_enrolled_in_same_session(self, auth_token, actee, actor_sur_id, actee_sur_id):
        """
        Returns True if the actor and the actee are both enrolled in the same
        session, for which actor is in the session_user_role actor_sur, and
        actee is in the session_user_role actee_sur.  Returns False otherwise.

        This method is only for use when the actee is a user.
        
        @param actee      A user object that we are evaluation authorization for
        @param actor_sur_id  The primary key of the session_user_role with which the
                actor should be enrolled in the session
        @param actee_sur_id  The primary key of the session_user_role with which
                the actee should be enrolled in the session
        """

        if not isinstance(actee, facade.models.User):
            raise exceptions.InvalidActeeTypeException()
        actee_sessions = set(facade.models.Session.objects.filter(
            session_user_role_requirements__assignments__user__id=actee.id,
            session_user_role_requirements__session_user_role__id=actee_sur_id
            ).values_list('id', flat=True))
        actor_sessions = set(facade.models.Session.objects.filter(
            session_user_role_requirements__assignments__user__id=auth_token.user.id,
            session_user_role_requirements__session_user_role__id=actor_sur_id
            ).values_list('id', flat = True))
        # The union of the two sets will be the set of sessions that they
        # are both enrolled in.  If this is not the empty set, then return True
        if actor_sessions & actee_sessions:
            return True
        return False

    def actor_is_acting_upon_themselves(self, auth_token, actee):
        """
        Returns True if the actor is a valid authenticated user in
        the system who is acting upon themselves.
        
        @param actee  A user object that we wish to compare the actor to
        """

        if not isinstance(actee, facade.models.User):
            raise exceptions.InvalidActeeTypeException()
        if auth_token.user.id == actee.id:
            return True
        return False

    def actor_is_instructor_manager_of_actee(self, auth_token, actee):
        """
        Returns True if the actor is the instructor manager for a product
        line in which the actee is an instructor.
        
        @param actee      A user object that we are evaluation authorization for
        """

        if not isinstance(actee, facade.models.User):
            raise exceptions.InvalidActeeTypeException()
        actee_product_lines_instructor_in = set(
            facade.models.ProductLine.objects.filter(
                instructors__id__exact=actee.id).values_list('id', flat=True))
        actor_product_lines_im_for = set(
            facade.models.ProductLine.objects.filter(
                instructor_managers__id__exact=auth_token.user.id
            ).values_list('id', flat = True))
        if actor_product_lines_im_for & actee_product_lines_instructor_in:
            return True
        return False

    def actor_is_product_line_manager_of_user(self, auth_token, actee):
        """
        Returns True if the actor is the product line manager for a
        product line in which the actee is an instructor.
        
        @param actee      A user object that we are evaluation authorization for
        """

        if not isinstance(actee, facade.models.User):
            raise exceptions.InvalidActeeTypeException()
        actee_product_lines_instructor_in = set(
            facade.models.ProductLine.objects.filter(
                instructors__id__exact=actee.id).values_list('id', flat=True))
        actor_product_lines_plm_for = set(
            facade.models.ProductLine.objects.filter(
                managers__id__exact=auth_token.user.id
            ).values_list('id', flat=True))
        if actor_product_lines_plm_for & actee_product_lines_instructor_in:
            return True
        return False

    #################################################################################
    #
    # Methods for which actee is a venue
    #
    #################################################################################

    def actor_is_venue_creator(self, auth_token, actee):
        """
        Returns True if the actor is the user who created the venue, which is discovered by
        examining the venue's blame
        """
        if not isinstance(actee, facade.models.Venue):
            raise exceptions.InvalidActeeTypeException()
        try:
            if auth_token.user.id == actee.blame.user.id:
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    #################################################################################
    #
    # Methods for which actee is None
    #
    #################################################################################
    
    @does_not_use_actee
    def actor_is_authenticated(self, auth_token, actee=None):
        """
        Returns True if the actor is an authenticated user in our system.
        
        @param actee  Not used by this method, and defaults to None 
        """

        if self.actor_is_guest(auth_token, actee):
            return False
        return True

    @does_not_use_actee
    @allow_guests
    def actor_is_guest(self, auth_token, actee=None):
        """
        Returns True if the actor is a guest.
        
        @param actee  Not used by this method, and defaults to None 
        """
        # Determine whether the actor is a guest or not, by testing to
        # see whether they are an authenticated user or not
        if isinstance(auth_token, facade.models.AuthToken):
            return False
        return True

    @does_not_use_actee
    def actor_member_of_group(self, auth_token, actee, group_id):
        """
        Returns True if the actor is a member of the specified group, False otherwise.
        
        @param actee      Not used by this method, but must be passed anyway as
                per authorization system requirements
        @param group_id   The primary key of the group we wish to test membership in
        """
        group_object = Utils.find_by_id(group_id, facade.models.Group)
        if group_object.users.filter(id=auth_token.user.id).exists():
            return True
        return False

    @does_not_use_actee
    def actor_status_check(self, auth_token, actee, status):
        """
        Returns True if the actor's status is equal to the specified status.

        @param actee    Not used by this method
        @type actee     user
        @param status   The status value that we want to know if the user has or not
        @type status    string
        @return         True if the actor's status is equal to the specified status, false otherwise.
        """
        if auth_token.user.status == status:
            return True
        return False

    @does_not_use_actee
    @allow_guests
    def actor_is_anybody(self, auth_token, actee=None):
        """
        Returns True no matter what, which will work for both guests and authenticated users.
        """

        return True

    #################################################################################
    #
    # Methods for which actee is of a configurable type
    #
    #################################################################################
    @allow_guests
    def actees_attribute_is_set_to(self, auth_token, actee, actee_model_name, attribute_name, attribute_value):
        """
        This complicatedly name method exists to be a bit generically useful.  It will examine actee,
        ensuring that it is of type actee_model_name.  It will then ensure that attribute_name's value is
        equal to attribute_value.
        
        ** Note: This depends on the model class's (or at least its parent class) being in facade.models. **

        @param auth_token       The authentication token of the acting user.  Guests are allowed, and so this method does not use the auth_token
        @type auth_token        facade.models.AuthToken
        @param actee            The object in question
        @type actee             pr_models.PRModel
        @param actee_model_name The name of the type of the model that this check is supposed to be applied to
        @type actee_model_name  str
        @param attribute_name   The name of the attribute on actee that we want do perform a comparison on
        @type attribute_name    str
        @param attribute_value  The value that actee's attribute should be compared to
        @type attribute_value   Many types are allowed (string, boolean, int, etc.)
        """
        try:
            if not isinstance(actee, getattr(facade.models, actee_model_name)):
                raise exceptions.InvalidActeeTypeException()
            if getattr(actee, attribute_name) == attribute_value:
                return True
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

    @allow_guests
    def actees_foreign_key_object_has_attribute_set_to(self, auth_token, actee, actee_model_name, attribute_name, foreign_object_attribute_name,
            foreign_object_attribute_value):
        """
        This complicatedly name method exists to be a bit generically useful.  It will examine actee,
        ensuring that it is of type actee_model_name.  It will then follow a foreign key relationship,
        actee.foreign_object_attribute_name, and ensure that that attribute's value is equal to
        foreign_object_attribute_value.
         
        ** Note: This depends on the model class's (or at least its parent class) being in facade.models. **

        @param auth_token                       The authentication token of the acting user.  Guests are allowed, and so this method does not use the auth_token
        @type auth_token                        facade.models.AuthToken
        @param actee                            The object in question
        @type actee                             pr_models.PRModel
        @param actee_model_name                 The name of the type of the model that this check is supposed to be applied to
        @type actee_model_name                  str
        @param attribute_name                   The name of the attribute on actee that we can use to retrieve the foreign object
        @type attribute_name                    str
        @param foreign_object_attribute_name    The name of the attribute on actee that will lead us to the foreign object we care about
        @type foreign_object_attribute_name     str
        @param foreign_object_attribute_value   The value that the foriegn object's attribute should be compared to
        @type foreign_object_attribute_value    Many types are allowed (string, boolean, int, etc.)
        """
        try:
            if not isinstance(actee, getattr(facade.models, actee_model_name)):
                raise exceptions.InvalidActeeTypeException()
            foreign_object = getattr(actee, attribute_name)
            return self.actees_attribute_is_set_to(auth_token, foreign_object, foreign_object.__class__.__name__, foreign_object_attribute_name,
                foreign_object_attribute_value)
        except ObjectDoesNotExist:
            pass
        except AttributeError:
            pass
        return False

# vim:tabstop=4 shiftwidth=4 expandtab
