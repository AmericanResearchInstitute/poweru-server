from __future__ import with_statement
"""
User manager class

:copyright: Copyright 2009 American Research Institute, Inc.
"""
__docformat__ = "restructuredtext en"

from datetime import date, datetime, timedelta
import hashlib
import logging
import os
import random
import re
from recaptcha.client import captcha
import string
import time
import threading
import uuid
import urllib2

import ldap

from django.conf import settings

from pr_services import exceptions
from pr_services.pr_models import queryset_empty
from pr_services import pr_time
from pr_services import storage
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
from pr_services.utils import upload
from pr_services.utils import Utils
from pr_services import middleware
from pr_messaging import send_message
import facade

class UserPhotoUploadForm(upload.FileUploadForm):
    pass

class UserManager(ObjectManager):
    """
    Manage all Users in the Power Reg system.
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        #: Dictionary of attribute names and the functions used to get them
        self.getters.update({
            'alleged_organization' : 'get_general',
            'billing_address' : 'get_address',
            'biography' : 'get_general',
            'color_code' : 'get_general',
            'completed_curriculum_enrollments' : 'get_general',
            'credentials' : 'get_many_to_one',
            'default_username_and_domain' : 'get_general',
            'domains' : 'get_many_to_many',
            'domain_affiliations' : 'get_many_to_one',
            'email' : 'get_general',
            'email2' : 'get_general',
            'enable_paypal' : 'get_general',
            'first_name' : 'get_general',
            'full_name' : 'get_general',
            'groups' : 'get_many_to_many',
            'incomplete_curriculum_enrollments' : 'get_general',
            'is_staff' : 'get_general',
            'last_name' : 'get_general',
            'middle_name' : 'get_general',
            'name_suffix' : 'get_general',
            'organizations' : 'get_many_to_many',
            'owned_userorgroles' : 'get_many_to_one',
            'paypal_address' : 'get_general',
            'phone' : 'get_general',
            'phone2' : 'get_general',
            'phone3' : 'get_general',
            'photo_url' : 'get_photo_url',
            'preferred_venues' : 'get_many_to_many',
            'product_lines_instructor_for' : 'get_many_to_many',
            'product_lines_instructor_manager_for' : 'get_many_to_many',
            'product_lines_managed' : 'get_many_to_many',
            'roles' : 'get_many_to_many',
            'session_user_role_requirements' : 'get_session_user_role_requirements_from_user',
            'shipping_address' : 'get_address',
            'status' : 'get_general',
            'suppress_emails' : 'get_general',
            'title' : 'get_general',
            'url' : 'get_general',
            'username' : 'get_general',
        })
        #: Dictionary of attribute names and the functions used to set them
        self.setters.update({
            'alleged_organization' : 'set_general',
            'billing_address' : 'set_address',
            'biography' : 'set_general',
            'color_code' : 'set_general',
            'credentials' : 'set_many',
            'email' : 'set_general',
            'email2' : 'set_general',
            'enable_paypal' : 'set_general',
            'first_name' : 'set_general',
            'groups' : 'set_many',
            'is_staff' : 'set_general',
            'last_name' : 'set_general',
            'middle_name' : 'set_general',
            'name_suffix' : 'set_general',
            'organizations' : 'set_many',
            'paypal_address' : 'set_general',
            'phone' : 'set_general',
            'phone2' : 'set_general',
            'phone3' : 'set_general',
            'photo_url' : 'set_forbidden', # placeholder
            'preferred_venues' : 'set_many',
            'roles' : 'set_many',
            'shipping_address' : 'set_address',
            'status' : 'set_status',
            'suppress_emails': 'set_general',
            'title' : 'set_general',
            'url' : 'set_general',
        })
        self.blame_manager = facade.managers.BlameManager()
        self.my_django_model = facade.models.User
        self.user_model_name = self.my_django_model().__class__.__name__
        if hasattr(settings, 'LDAP_SCHEMA'):
            self.ldap_user_model_name = settings.LDAP_SCHEMA[self.user_model_name]['ldap_object_class']
            if hasattr(settings, 'LDAP_CACERT_FILE') and settings.LDAP_CACERT_FILE:
                ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.LDAP_CACERT_FILE)
            self.ldap_connection = ldap.initialize(settings.LDAP_URL)
        self.photo_storage_engine = storage.UserPhotoStorage()
    
    @service_method
    def check_password_against_policy(self, proposed_password, messages=None):
        """
        Checks a proposed password against the password policy, raising a
        PasswordPolicyViolation exception with details about what was wrong
        if it doesn't meet the requirements.
        
        Automatically generated passwords are generally checked against
        password policy through this method.  If you are overridding this
        method to provide a more interesting password policy, please also
        modify the _generate_password() method so that it always generates
        valid passwords.
        
        Should be overridden by variants when they have password policies.
        
        :param proposed_password: proposed password to check
        :type proposed_password: string
        :param messages: messages already accumulated (useful for extending without overriding entirely)
        :type messages: None or list
        
        :returns: None
        
        :raises: pr_services.exceptions.PasswordPolicyViolation if the password policy wasn't
                 met.  The exception should have a 'details' attribute, which in turn should
                 have a 'messages' key, which should have information about what, specifically,
                 wasn't kosher.
        """

        if messages is None:
            messages = []
        if len(proposed_password) < 1:
            messages.append('passwords must be at least one character long')
        forbidden_characters_seen = set()
        for _ in proposed_password:
            if not _ in settings.PASSWORD_CHARACTER_WHITELIST:
                forbidden_characters_seen.add(_)
        forbidden_characters_string = ''
        for _ in forbidden_characters_seen:
            forbidden_characters_string += _
        if forbidden_characters_seen:
            messages.append(u'the following forbidden characters were used: "%s"' %
                forbidden_characters_string)
                 
        if messages:
            raise exceptions.PasswordPolicyViolation(messages)
    
    def _generate_password(self):
        """
        Generates a password, which must meet the password requirements as defined by the
        check_password_against_policy() method.
        """
        
        return self._generate_random_string(8,
            string.ascii_lowercase + string.ascii_uppercase + string.digits)

    @service_method
    def create(self, auth_token, username, initial_password, title, first_name, last_name,
               phone, email, status, optional_attributes=None):
        """
        Create a new User in the system.
        
        to email the user's password to them, including 'send_password' : True in optional_attributes
        
        :param auth_token:            The authentication token of the acting User.  Can be
                                      passed as a blank string to indicate a guest User.
        :param username:              The username
        :param initial_password:      The initial password
        :param title:                 String: Mr, Mrs, Dr, etc
        :param first_name:            First Name
        :param last_name:             Last Name
        :param phone:                 Phone Number
        :param email:                 Email address
        :param status:                What status the User should be created as
        :type status:                 string
        :param optional_attributes:   dictionary of optional attribute values indexed by name,
            including domain
        :return:                      User instance
        
        :raises: pr_services.exceptions.PasswordPolicyViolation
        """

        if not optional_attributes:
            optional_attributes = dict()
        else:
            optional_attributes = optional_attributes.copy()

        domain = optional_attributes.pop('domain', u'local')
        challenge = optional_attributes.pop('recaptcha_challenge', '')
        response = optional_attributes.pop('recaptcha_response', '')
        send_password = optional_attributes.pop('send_password', False)

        try:
            domain_object = facade.models.Domain.objects.get(name=domain)
        except facade.models.Domain.DoesNotExist:
            raise exceptions.ObjectNotFoundException('domain')
        
        # FIXME: there should be a better way to determine whether to exempt
        # a password from being checked against requirements.  For example,
        # we may want to support multiple LDAP directories.
        if domain != 'LDAP':
            self.check_password_against_policy(initial_password)

        # calculate a cryptographic hash of the User's password
        # for storage in the db
        salt = self._generate_password_salt()
        password_hash = Utils._hash(initial_password + salt, 'SHA-512')
        password_hash_type = 'SHA-512'

        u = self.my_django_model(last_name=last_name, first_name=first_name, title=title, phone=phone,
            email=email, status=status)
        u.save() # So we can do many-to-many relationships

        da = facade.models.DomainAffiliation.objects.create(user=u, domain=domain_object, password_salt=salt,
            username=username, password_hash=password_hash, password_hash_type=password_hash_type, default=True)
        
        # if this User was created by an anonymous User, get an auth token for
        # the User that was created, so that we can set the
        # blame to the newly created User
        should_unauth = False
        if not isinstance(auth_token, facade.models.AuthToken):
            should_unauth = True
            old_auth_token = auth_token
            auth_token = self._generate_auth_token(da)
        
        user_blame = self.blame_manager.create(auth_token)
        u.blame = user_blame
        u.owner = u
        
        facade.subsystems.Setter(auth_token, self, u, optional_attributes)
        # we set groups manualy because self-registering users don't have
        # permission to do it
        default_groups = facade.models.Group.objects.filter(default=True).\
            values_list('id', flat=True)
        u.groups.add(*default_groups)
        u.save() # To save any non-many-to-many attribute changes

        self.authorizer.check_create_permissions(auth_token, u)

        if should_unauth:
            self.logout(auth_token)
            auth_token = old_auth_token
            if not self.validate_recaptcha(challenge, response):
                raise exceptions.PermissionDeniedException()
            if status != 'pending':
                raise exceptions.PermissionDeniedException()

        # figure out what orgs will be assigned when the user gets confirmed
        # so that we can use them in the confimation and/or password email
        organizations = []
        for email in filter(None, (u.email, u.email2)):
            email_domain = email.split('@', 1)[1]
            for org_email_domain in facade.models.OrgEmailDomain.objects.filter(email_domain=email_domain):
                organizations.append(org_email_domain.organization)
        # build the context we need for the template rendering
        context = {
            'user' : u,
            'date' : date.today(),
        }
        if len(organizations):
            context['organization'] = organizations[0]
 
        if send_password:
            context['initial_password'] = initial_password
            send_message(message_type='initial-password', recipient=u,
                context=context)

        if u.confirmation_code:
            context['confirmation_code'] = u.confirmation_code
            send_message(message_type='user-confirmation', recipient=u,
                context=context)

        return u

    @service_method
    def change_password(self, auth_token, user_id, new_password, old_password=None,
        domain=u'local'):
        """
        Change a User's password.
        
        :param user_id:      The id of the User who's password we want to change
        :param new_password: The User's new password
        :type new_password:  string
        :param old_password: The User's old password.  This must be correct if passed.
                             If not passed, the User with the auth_token must have privilege
                             to alter the User's password
        :type old_password:  string or none
        :param domain:       the User's domain
        :type domain:        string
        
        :raises: pr_services.exceptions.PasswordPolicyViolation
        """

        if domain != 'local':
            raise exceptions.CannotChangeForeignPasswordException()
        da = facade.models.DomainAffiliation.objects.get(user__id=user_id, domain__name=domain)
        actee = da.user
        if old_password:
            # First we check the old password to make sure it is correct
            self._authenticate(da.username, old_password, domain)
        else:
            # Check that the user has permission to change other users passowrds
            self.authorizer.check_arbitrary_permissions(auth_token, 
                'change_password_of_other_users')
        # Then we set the new password (we won't get here if the previous line
        # raised an exception)
        self._change_password(da, new_password)
    
    @service_method
    def generate_username(self, auth_token, first_name, last_name, domain=u'local'):
        """
        Return a valid system username that is generated based on the new User's name.

        :param first_name:  The new User's first name
        :type first_name: string
        :param last_name:    The new User's last name
        :type last_name: string
        :param domain: the domain to generate the username for
        :type domain: string
        
        :return:             A suggested username for the new User that will be valid
        """

        self.authorizer.check_arbitrary_permissions(auth_token, 'check_usernames')
        first_name = string.lstrip(first_name)
        suggested_username = (first_name[0:1] + last_name).lower()
        suggested_username = Utils.asciify(suggested_username)
        return self.suggest_username_like(auth_token, suggested_username, domain)

    @service_method
    def suggest_username_like(self, auth_token, requested_username, domain=u'local'):
        """
        Return a username that is valid for the system (i.e., no invalid characters
        and doesn't clash with an existing username).

        :param requested_username:  The username that the suggested username should be based on
        :type requested_username: string
        :param domain: the domain for which to suggest the username
        :type domain: string
        
        :return: suggested_username  The username that should be valid for the new system
        """

        self.authorizer.check_arbitrary_permissions(auth_token, 'check_usernames')
        suggested_username = requested_username
        for c in suggested_username:
            if c.isspace():
                suggested_username = suggested_username.replace(str(c), '')
        for c in facade.models.DomainAffiliation.USERNAME_ILLEGAL_CHARACTERS:
            suggested_username = suggested_username.replace(str(c), '')
        # Check to see if we already have the current username
        if not queryset_empty(facade.models.DomainAffiliation.objects.filter(username=suggested_username, domain__name=domain)):
            # We can append a suffix on the end of the requested username and try that.
            # Let's try starting with 1.
            integer_suffix = 1
            found_good_username = False
            # While we haven't found a good username, let's keep trying with different
            # suffixes.
            while not found_good_username:
                if queryset_empty(facade.models.DomainAffiliation.objects.filter(username=suggested_username+str(integer_suffix), domain__name=domain)):
                    # We've found a good username, so let's quit the while and return it
                    found_good_username = True
                    suggested_username = suggested_username + str(integer_suffix)
                else:
                    # Try the next suffix
                    integer_suffix += 1
        return suggested_username

    def _change_password(self, domain_affiliation, new_password):
        """
        Common method to change a User's password to a new value
        
        :param domain_affiliation:  Instance of the DomainAffiliation for which we wish to change the password
        :param new_password:        the new password
        :type new_password: string
        
        :raises: pr_services.exceptions.PasswordPolicyViolation
        """
        
        self.check_password_against_policy(new_password)
        domain_affiliation.password_hash_type = 'SHA-512'
        salt = self._generate_password_salt()
        domain_affiliation.password_salt = salt
        domain_affiliation.password_hash = Utils._hash(new_password + salt, 'SHA-512')
        domain_affiliation.save()

    @service_method
    def confirm_email(self, confirmation_code):
        """
        Validate a confirmation code sent to a new user via email when they
        registered.  If the confirmation code is valid, hasn't expired, and
        hasn't already been used, change the user status to active.  Optionally
        return an auth token to automatically log the user in.
        """
        try:
            u = self.my_django_model.objects.get(confirmation_code=confirmation_code)
        except self.my_django_model.DoesNotExist:
            raise exceptions.UserConfirmationException(msg='invalid confirmation code')
        user_confirmation_days = getattr(settings, 'USER_CONFIRMATION_DAYS', 7)
        if u.status != 'pending':
            raise exceptions.UserConfirmationException(msg='user is already confirmed')
        elif (datetime.now() - timedelta(days=user_confirmation_days)) > u.create_timestamp:
            raise exceptions.UserConfirmationException(msg='confirmation code has expired')
        else:
            u.change_status('active')
            if getattr(settings, 'ASSIGN_ORG_ROLES_FROM_EMAIL', False):
                u.assign_org_roles_from_email()
            u.save()
            if getattr(settings, 'USER_CONFIRMATION_AUTO_LOGIN', True):
                ud = u.default_username_and_domain
                da = self._find_da_by_username(ud['username'], ud['domain'])
                return self._generate_auth_token(da)

    @service_method
    def reset_password(self, username, email, domain=u'local'):
        """
        Resets a user's password.  This is used for when the user
        can't remember their password and they need a new one
        generated.  It will generate a random 16 character string,
        update the password hash, and then e-mail the User with
        the new password.  The User must supply their username and
        at least one valid e-mail address (must match one of the
        e-mail addresses we have on file for the User.)
        
        :param username: The username of the user who wants their
                        password to be reset
        :type username:  string
        :param email:    An email address that is on file for the
                        user who is resetting their password (this
                        acts as a [weak] safegard against attackers).
                        We will send the new password to this email address.
        :type email:     string
        :param domain:   the user's domain
        :type domain:    string
        
        :raises: pr_services.exceptions.PasswordPolicyViolation (however, if this is raised,
                 then there is a bug in the _generate_password() method, the
                 check_password_against_policy() method, or both)
        """

        da = self._find_da_by_username(username, domain)
            
        actee = da.user
        # domain names are case insensitive as per RFC 4343
        # email addresses are usually case sensitive, and are for qinetiq always
        if email.lower() not in [unicode(actee.email).lower(), unicode(actee.email2).lower()]:
            raise exceptions.ObjectNotFoundException('EmailAddress')
        # Generate a new random, 16-character string
        new_password = self._generate_password()
        self._change_password(da, new_password)
        if email != actee.email:
            recipient = email
        else:
            recipient = actee.email
        context = {
            'new_password': new_password,
            'user' : actee,
            'date' : date.today(),
        }
        orgs = actee.organizations.all()
        if len(orgs):
            context['organization'] = orgs[0]
        send_message(message_type='password-reset', context=context,
                     recipient=recipient)

    def _generate_password_salt(self):
        """
        Generate a random string to be used for a password salt.

        :return: password salt
        :rtype: string
        """
        salt_chars = './' + string.ascii_letters + string.digits
        salt = ''
        for i in range(8):
            salt += salt_chars[random.randrange(64)]
        return salt

    @service_method
    def batch_create(self, auth_token, account_detail_list):
        """
        Create multiple User accounts at once
        
        :param account_detail_list:   Array of structs containing the arguments taken
                                      by the create() method indexed by field name

        :return:     Struct of usernames indexed by primary keys for accounts that were created
        """

        accounts = {}
        for account_details in account_detail_list:
            account_details['auth_token'] = auth_token
            o = self.create(**account_details)
            accounts[o.id] = o.domain_affiliations.all()[0].username
            o.blame = self.blame_manager.create(auth_token)
            o.save()
        return accounts

    @service_method
    def login(self, username, password, domain=u'local'):
        """
        Authenticate a user by password, returning an authentication token if successful.
        
        :param username:                        username of the user to authenticate
        :type username:                         string
        :param password:                        password to use for authentication
        :type password:                         string
        :param domain:                          name of the domain to use for the username given
        :type domain:                           string
        
        :return:                                a dictionary containing a session_id/auth token
                                                string and it's expiration date, indexed
                                                by 'auth_token' and 'expiration'
        :rtype:                                 dict
        
        :raises AuthenticationFailureException: on an incorrect username or password
        :raises UserInactiveException:          when an inactive user tries to authenticate
        :raises UserSuspendedException:         when a suspended user tries to authenticate
        """

        da = self._authenticate(username, password, domain)

        authenticated_session = self._generate_auth_token(da)

        if da.domain.name == 'LDAP':
            self._collect_ldap_information(da)

        return self._create_user_info_dict(authenticated_session)

    def _generate_auth_token(self, domain_affiliation):
        """
        create an AuthToken based on a DomainAffiliation
        """
        # store authenticated session data in the db
        authenticated_session = facade.models.AuthToken()

        # associate the auth token with the User
        authenticated_session.domain_affiliation = domain_affiliation
        authenticated_session.session_id = self._generate_session_id()

        # record relevant timestamps
        authenticated_session.issue_timestamp = datetime.utcnow()
        authenticated_session.number_of_renewals = 0
        authenticated_session.time_of_expiration = authenticated_session.issue_timestamp + timedelta(minutes=settings.AUTH_TOKEN_EXPIRATION_INTERVAL)

        request = middleware.get_current_request()
        if request is not None and 'REMOTE_ADDR' in request.META.keys():
            authenticated_session.ip = request.META['REMOTE_ADDR']

        authenticated_session.save()

        return authenticated_session

    @service_method
    def redeem_auth_token_voucher(self, voucher):
        """
        Obtain an AuthToken in exchange for an AuthTokenVoucher. The voucher is good for only one
        use, and this method has the same effect as calling login() with the proper credentials.

        :param voucher: unique identifier for the voucher
        :type voucher: string

        :return:                                a dictionary containing a session_id/auth token string and it's expiration date, indexed by 'auth_token'
                                                and 'expiration'
        :rtype:                                 dict
        """
        try:
            at_voucher = facade.models.AuthTokenVoucher.objects.get(session_id=voucher)
        except facade.models.AuthTokenVoucher.DoesNotExist:
            raise exceptions.ObjectNotFoundException('AuthTokenVoucher')

        now = datetime.utcnow()
        if at_voucher.time_of_expiration < now:
            # It would be nice to delete the voucher here. But, the exception that is about to be raised
            # will roll back any data changes we make.
            time_since_expiration = now - at_voucher.time_of_expiration
            seconds_since_expiration = time_since_expiration.seconds + time_since_expiration.days * 86400
            self.logger.info('redemption of AuthTokenVoucher for user %s of domain %s failed because it expired %d seconds ago' % (
                at_voucher.domain_affiliation.username, at_voucher.domain_affiliation.domain.name, seconds_since_expiration))
            self._fail_authentication(at_voucher.domain_affiliation.username, at_voucher.domain_affiliation.domain.name)

        da = at_voucher.domain_affiliation
        at = self._generate_auth_token(at_voucher.domain_affiliation)
        at_voucher.delete()
        self.logger.info('domain %s obtained an AuthToken for user %s' % (da.domain.name, da.username))
        return {'auth_token' : at.session_id,
            'expiration' : at.time_of_expiration.replace(microsecond=0, tzinfo=pr_time.UTC()).isoformat()}

    @service_method
    def obtain_auth_token_voucher(self, domain, username, password):
        """
        Each domain is authorized to call this method from no more than one IP address.
        The return value of this method should be passed to a user interface so that
        it may call redeem_auth_token_voucher(). This value is the only data you need
        to give a UI in order for it to start an authenticated session, although a specific
        UI implementation may require additional data for other purposes.

        :param domain:      name of the domain
        :type domain:       string
        :param username:    username within the given domain
        :type username:     string
        :param password:    The password assigned to the domain
        :type password:     string

        :return:            32-character voucher identifier that can be passed to the redeem_auth_token_voucher() method
        :rtype:             string

        :raises pr_services.pr_exceptions.ObjectNotFoundException: (error code 97) if the Domain or DomainAffiliation was not found
        :raises pr_services.pr_exceptions.AuthenticationFailureException: (error code 17) if the password is incorrect or the
            DomainAffiliation doesn't allow the domain's authentication agent to log in
            the user
        """
        try:
            domain_object = facade.models.Domain.objects.get(name=domain)
        except facade.models.Domain.DoesNotExist:
            raise exceptions.ObjectNotFoundException('Domain')

        # verify that the request comes from an authorized ip address
        ip = middleware.get_current_request().META['REMOTE_ADDR']
        if ip != domain_object.authentication_ip:
            self.logger.info('domain %s tried to obtain an AuthTokenVoucher for username %s from invalid ip address %s' % (
                domain_object.name, username, ip))
            self._fail_authentication('', domain_object.name)

        # verify the password
        if not Utils._verify_hash(password, '', domain_object.password_hash_type, domain_object.authentication_password_hash):
            self._fail_authentication('', domain_object.name)

        try:
            da = facade.models.DomainAffiliation.objects.get(username=username, domain__name=domain_object.name)
        except facade.models.DomainAffiliation.DoesNotExist:
            raise exceptions.ObjectNotFoundException('DomainAffiliation')

        # verify that the user has agreed to this
        if not da.may_log_me_in:
            self.logger.info('domain %s tried to obtain an AuthTokenVoucher for username %s, who has not granted permission' % (
                domain_object.name, username))
            self._fail_authentication('', domain_object.name)

        now = datetime.utcnow().replace(microsecond=0)
        atv = facade.models.AuthTokenVoucher.objects.create(session_id=self._generate_session_id(),
            domain_affiliation=da, issue_timestamp=now, time_of_expiration=(now+timedelta(seconds=settings.AUTH_TOKEN_VOUCHER_LIFE)))

        return atv.session_id

    @service_method
    def relogin(self, auth_token):
        """
        renew a current authenticated session. We used to require full authentication credentials,
        but we now require none.  Please note the deprecation statements below.
        
        :param auth_token:  The auth_token of the session to be renewed
        :type auth_token:   facade.models.AuthToken
        
        :return:            dictionary containing values 'auth_token', 'expiration', 'username', 'domain', 'id', 'groups'
        :rtype:             dict
        """

        if not isinstance(auth_token, facade.models.AuthToken) or \
                isinstance(auth_token, facade.models.SingleUseAuthToken):
            self._fail_authentication('')

        u = auth_token.user

        if u.status == 'inactive':
            raise exceptions.UserInactiveException
        if u.status == 'suspended':
            raise exceptions.UserSuspendedException
        if auth_token.time_of_expiration < datetime.utcnow():
            self._fail_authentication('')
        
        auth_token.session_id = self._generate_session_id()
        auth_token.number_of_renewals += 1
        auth_token.renewal_timestamp = datetime.utcnow()
        auth_token.time_of_expiration = auth_token.renewal_timestamp + timedelta(minutes=settings.AUTH_TOKEN_EXPIRATION_INTERVAL)
        auth_token.save()

        return self._create_user_info_dict(auth_token)

    @service_method
    def obtain_single_use_auth_token(self, auth_token):
        """Given a valid AuthToken, returns a new SingleUseAuthToken"""

        if not isinstance(auth_token, facade.models.AuthToken) or \
                isinstance(auth_token, facade.models.SingleUseAuthToken):
            self._fail_authentication('')

        u = auth_token.user
        if u.status == 'inactive':
            raise exceptions.UserInactiveException
        if u.status == 'suspended':
            raise exceptions.UserSuspendedException
        if auth_token.time_of_expiration < datetime.utcnow():
            self._fail_authentication('')

        now = datetime.utcnow()
        kwargs = {
            'domain_affiliation' : auth_token.domain_affiliation,
            'session_id' : self._generate_session_id(),
            'number_of_renewals' : 0,
            'issue_timestamp' : now,
            'time_of_expiration' : now + timedelta(
                minutes=settings.AUTH_TOKEN_SINGLE_USE_EXPIRATION_INTERVAL),
        }
        request = middleware.get_current_request()
        if request is not None and request.META.has_key('REMOTE_ADDR'):
            kwargs['ip'] = request.META['REMOTE_ADDR']
        suat = facade.models.SingleUseAuthToken.objects.create(**kwargs)
        return suat.session_id

    def _create_user_info_dict(self, auth_token):
        """
        creates and returns a dictionary with all of the user information that
        may be useful upon login.

        :param auth_token:  The auth_token of the session
        :type auth_token:   facade.models.AuthToken
        :return:            dictionary containing values 'auth_token', 'expiration', 'username', 'domain', 'id', 'groups'
        :rtype:             dict
        """
        da = auth_token.domain_affiliation
        groups = [{'id':group.id, 'name':group.name} for group in auth_token.user.groups.all()]

        ret = self.get_filtered(auth_token, {'exact' : {'id':da.user.id}}, [
            'id', 'groups', 'first_name', 'last_name',
            'title', 'email', 'phone', 'status', 'organizations', 'groups'])

        ret = Utils.merge_queries(ret, facade.managers.GroupManager(), auth_token, ['name'], 'groups')[0]

        ret.update({'auth_token' : auth_token.session_id,
                    'username' : da.username,
                    'domain' : da.domain.name,
                    'expiration' : auth_token.time_of_expiration.replace(microsecond=0, tzinfo=pr_time.UTC()).isoformat()})

        return ret
            
    @service_method
    def get_authenticated_user(self, auth_token):
        """
        Return the username, domain, id of the user associated with
        the auth_token as well as the time of expiration of the
        auth_token.

        :param auth_token:  A valid auth_token
        :type auth_token:   facade.models.AuthToken

        :return:            a dictionary containing the 'username', 'domain', 'id' and
                            'expiration' associated with the given auth_token
        :rtype:             dict
        """

        if not isinstance(auth_token, facade.models.AuthToken):
            time.sleep(settings.AUTHENTICATION_FAILURE_DELAY)
            raise exceptions.AuthenticationFailureException()

        da = auth_token.domain_affiliation
        return {'username' : da.username, 'domain' : da.domain.name, 'id' : da.user.id,
            'expiration' : auth_token.time_of_expiration.replace(microsecond=0,
            tzinfo=pr_time.UTC()).isoformat()}

    def _collect_ldap_information(self, domain_affiliation):
        """
        Using the global LDAP settings, attempt to query the LDAP server and
        gather all the information we are allowed to gather about user, storing that
        information on our local copy.

        :param user: The user we want to know about
        :type user:  facade.models.User
        """
        try:
            user = domain_affiliation.user
            self._get_users_ldap_dn(domain_affiliation)
            ldap_results = self.ldap_connection.search_s(domain_affiliation.ldap_dn, ldap.SCOPE_SUBTREE, '(cn=%s)'%(domain_affiliation.username))
            # Assert that the length of the LDAP results is 1
            if len(ldap_results) != 1:
                if len(ldap_results) == 0:
                    # The user wasn't found in LDAP
                    raise exceptions.ForeignObjectNotFoundException('The user %s was not found in the remote directory.'%(domain_affiliation.username))
                raise exceptions.InternalErrorException('There was more than one record returned by LDAP for username %s'%domain_affiliation.username)
            ldap_results = ldap_results[0]
            user_ldap_schema = settings.LDAP_SCHEMA[self.user_model_name]['local_attributes']
            for user_field in user_ldap_schema.keys():
                try:
                    ldap_name = user_ldap_schema[user_field]['ldap_name']
                    if user_ldap_schema[user_field]['query_type'] == 'simple':
                        setattr(user, user_field, ldap_results[1][ldap_name][0])
                    elif user_ldap_schema[user_field]['query_type'] == 'many_to_many':
                        m2m_attr = getattr(user, user_field)
                        m2m_model = m2m_attr.model
                        m2m_attr.clear()
                        for m2m_item_name in ldap_results[1][ldap_name]:
                            try:
                                local_m2m_name = user_ldap_schema[user_field]['name_mapping'][m2m_item_name]
                                m2m_object = m2m_model.objects.get(name__iexact=local_m2m_name)
                                m2m_attr.add(m2m_object)
                            # This will happen when we don't have a group by the name of the LDAP user's groups, which will be frequent
                            except m2m_model.DoesNotExist:
                                continue
                            except KeyError:
                                # This will happen when the m2m_item_name is not in our search dict, i.e if a user is in a group that we don't care about
                                continue
                except KeyError: # This will happen if the ldap entry doesn't contain one of the attributes we care about
                    continue
            user.save()
        except ldap.NO_SUCH_OBJECT:
            # The user wasn't found in LDAP
            raise exceptions.ForeignObjectNotFoundException('The user %s was not found in the remote directory.'%(domain_affiliation.username))

    def _fail_authentication(self, username, domain=u'local'):
        """
        Any time authentication fails, this method gets called as a handler.
        It may do things like impose a time delay, lock an account after
        some number of consecutive failed attempts, and of course raise the
        appropriate exception.

        :param username:    The username that was used for authentication.
        :type  username:    string
        :param domain: the domain
        :type domain: string
        """
        
        time.sleep(settings.AUTHENTICATION_FAILURE_DELAY)
        raise exceptions.AuthenticationFailureException()

    def _generate_random_string(self, num_bytes, allowed_characters=string.hexdigits):
        """
        Generate a cryptographic quality pseudo-random string
        
        :param num_bytes: the number of bytes desired for the string
        """

        num_allowed_characters = len(allowed_characters)

        assert num_allowed_characters <= 256, ("pr_services.UserManager._generate_random_string()" +
            " needs to use more than one random byte at a time to be able to choose from your " +
            "list of %d allowed_characters.")

        pseudo_random_bytes = os.urandom(num_bytes)
        random_string = ''
        for byte in pseudo_random_bytes:
            random_string += allowed_characters[ord(byte) % num_allowed_characters]
        return random_string

    def _generate_session_id(self):
        """
        generate a unique session id
        """

        return uuid.uuid4().hex

    def _authenticate(self, username, password, domain='local'):
        """
        handle authentication.  This method will determine the authentication mechanism
        for the given domain and delegate authentication to mechanism-specific
        method.
        """
        try:
            domain_affiliation = self._find_da_by_username(username, domain)
        except exceptions.ObjectNotFoundException:
            self.logger.info('failed authentication due to User not found: username [%s] domain [%s]'%(username, domain))
            self._fail_authentication(username, domain)

        if domain_affiliation.user.status == 'pending' and domain_affiliation.user.confirmation_code:
            raise exceptions.UserConfirmationException(username, domain)
        if domain_affiliation.user.status == 'inactive':
            raise exceptions.UserInactiveException(username, domain)
        if domain_affiliation.user.status == 'suspended':
            raise exceptions.UserSuspendedException(username, domain)

        if domain_affiliation.domain.name == 'LDAP' and settings.LDAP_AUTHENTICATION == True:
            self._authenticate_ldap(domain_affiliation, password)
        elif domain_affiliation.domain.name == 'local':
            self._authenticate_local(domain_affiliation, password)
        else:
            self._fail_authentication(username, domain)

        return domain_affiliation

    def _authenticate_ldap(self, domain_affiliation, password):
        """
        check a supplied username and password against
        LDAP, succeeding quietly or raising
        an exception (typically AuthenticationFailureException,
        but an assertion may fail instead if the database contains
        two User records with the same username or some
        other invalid state)
        
        :param actee:   the User object
        :type actee:    facade.models.User
        """
        self._get_users_ldap_dn(domain_affiliation)
        try:
            self.ldap_connection.bind_s(domain_affiliation.ldap_dn, password, ldap.AUTH_SIMPLE)
        except ldap.INVALID_CREDENTIALS:
            self._fail_authentication(domain_affiliation.username, domain_affiliation.domain.name)
        except ldap.OTHER:
            raise exceptions.InternalErrorException('There was a problem communicating with the remote directory services system.')

    def _authenticate_local(self, domain_affiliation, password):
        """
        check a supplied username and password against
        the database, succeeding quietly or raising
        an exception (typically AuthenticationFailureException,
        but an assertion may fail instead if the database contains
        two User records with the same username or some
        other invalid state)
        
        :param actee:   the User object
        :type actee:    facade.models.User
        """
        if hasattr(domain_affiliation, 'password_salt') and domain_affiliation.password_salt is not None:
            salt = domain_affiliation.password_salt
        else:
            salt = ''

        if not Utils._verify_hash(password, salt, domain_affiliation.password_hash_type, domain_affiliation.password_hash):
            self._fail_authentication(domain_affiliation.username, domain_affiliation.domain.name)
    
        # If the user isn't using SHA-512, let's go ahead and update them to SHA-512 since they've authenticated
        if domain_affiliation.password_hash_type != 'SHA-512':
            self._change_password(domain_affiliation, password)

    @service_method
    def logout(self, auth_token):
        """
        unauthenticate a User (logout)
        
        :param auth_token: the auth token
        :type auth_token: facade.models.AuthToken
        
        This simply removes an auth token from the database.
        """

        if isinstance(auth_token, facade.models.AuthToken):
            auth_token.delete()

    def delete(self, auth_token, pr_object_id):
        """
        delete a User    We don't like this.  De-activate them instead.
                         Be nice to your sysadmin or database administrator
                         if you really, really want to do this.
        
        This overrides pr2_object_manager.delete()
        """

        raise exceptions.OperationNotPermittedException()

    def _deactivate(self, auth_token, user_id, domain=u'local'):
        """
        De-activate a User.
        
        :param user_id: id of User to deactivate
        :type user_id: int
        :param domain:   the domain
        :type domain:    string
        """

        u = self._find_by_id(user_id)
        u.change_status('inactive')
        u.save()

    def _find_da_by_username(self, username, domain=u'local', password=None):
        """
        Find a user by username/domain name. If they don't exist in LDAP but should, and
        settings.LDAP_CREATE_ON_LOGIN == True, the user will be automatically created
        and then logged in.

        :param username: the username
        :type username: string
        :param domain: the User's domain
        :type domain: string
        """
        try:
            return facade.models.DomainAffiliation.objects.get(username=username, domain__name=domain)
        except facade.models.DomainAffiliation.DoesNotExist:
            if domain == 'LDAP' and settings.LDAP_CREATE_ON_LOGIN == True:
                # If the user is supposed to be in LDAP, and our system settings say that we should create them if they don't exist, let's create them
                try:
                    ldap_dn = self._get_usernames_ldap_dn(username)
                    if password is None:
                        initial_password = ''
                    else:
                        initial_password = password
                    u = self.create('', username, initial_password, '', '', '', '', '', 'pending',
                        {'domain' : 'LDAP'})
                    u.change_status('active')
                    if getattr(settings, 'ASSIGN_ORG_ROLES_FROM_EMAIL', False):
                        u.assign_org_roles_from_email()
                    u.save()
                    self.logger.info('Automatically created user %s in domain %s'%(username, domain))
                    da = facade.models.DomainAffiliation.objects.get(username=username, domain__name=domain)
                    da.ldap_dn = ldap_dn
                    return da
                except ldap.NO_SUCH_OBJECT:
                    raise exceptions.ObjectNotFoundException(self.my_django_model.__class__.__name__)
            else:
                raise exceptions.ObjectNotFoundException(self.my_django_model.__class__.__name__)

    def _get_usernames_ldap_dn(self, username):
        """
        This method will query LDAP for the DN of the user specified by username.
        """
        self.ldap_connection.bind_s('cn=Anonymous', '', ldap.AUTH_SIMPLE)
        ldap_results = self.ldap_connection.search_s(settings.LDAP_BASE, ldap.SCOPE_SUBTREE, '(cn=%s)'%username)
        self.logger.debug('UserManager._get_usernames_ldap_dn(): ldap_results: [%s]' % str(ldap_results))
        if len(ldap_results) != 1:
            if len(ldap_results) == 0:
                raise exceptions.ObjectNotFoundException(self.my_django_model.__class__.__name__)
            raise exceptions.InternalErrorException('More than one result was returned when querying LDAP for username %s'%username)
        return ldap_results[0][0]

    def _get_users_ldap_dn(self, domain_affiliation):
        """
        This method will check to see if we already know the user's dn, and if not will attempt an anonymous bind to get the User's dn.  It will then add an attribute to the
        domain_affiliation, ldap_dn.
        """
        if not hasattr(domain_affiliation, 'ldap_dn') or domain_affiliation.ldap_dn is None:
            domain_affiliation.ldap_dn = self._get_usernames_ldap_dn(domain_affiliation.username)

    def upload_user_photo(self, request, auth_token=None, user_id=None):
        """Handle Image file uploads

        This method will stick the contents of the uploaded file (of which there
        must be exactly 1) onto the filesystem, using Django's "ImageField".

        This method does no validation by design, as that is expected to happen
        in the storage system

        :param request:   HttpRequest object from django

        """
        if request.method == 'GET':
            if auth_token is None:
                return upload._render_response_forbidden(request,
                    msg='Your request must include an auth token in its URL.')
            if user_id is None:
                return upload._render_response_bad_request(request,
                    msg='Your request must include a user ID as the last component of its URL.')
            return upload._render_response(request, 'upload_user_photo.html',
                {'title': 'User Photo Upload', 'form': UserPhotoUploadForm(),
                'user_id': user_id, 'auth_token': auth_token})

        return upload._upload_photo(request, self, 'user_id',
            storage.UserPhotoStorage(), auth_token, user_id)

    @service_method
    def admin_users_view(self, auth_token, pks=None):
        filters = {} if pks == None else {'member' : {'id' : pks}}
        ret = self.get_filtered(auth_token, filters, ['alleged_organization', 'default_username_and_domain', 'email', 'first_name', 'last_name', 'title', 'phone', 'status', 'groups', 'owned_userorgroles'])

        ret = Utils.merge_queries(ret, facade.managers.UserOrgRoleManager(), auth_token, ['role', 'role_name', 'organization', 'organization_name'], 'owned_userorgroles')

        return Utils.merge_queries(ret, facade.managers.GroupManager(), auth_token, 
            ['name'], 'groups')

    @service_method
    def get_users_by_group_name(self, auth_token, group_name, fields):
        user_ids = self.my_django_model.objects.filter(groups__name=group_name).values_list('id', flat=True)
        return self.get_filtered(auth_token, {'member' : {'id' : user_ids}}, fields)

    @service_method
    def get_recaptcha_challenge(self):
        html = urllib2.urlopen('%s/noscript?k=%s' %
            (captcha.API_SSL_SERVER, settings.RECAPTCHA_PUBLIC_KEY)).read()
        challenge = re.search('<input[^>]+?name="recaptcha_challenge_field"'+
            '[^>]+?value="([0-9A-Za-z_-]+)"', html).group(1)
        return [challenge,
            '%s/image?c=%s' % (captcha.API_SSL_SERVER, challenge)]

    def validate_recaptcha(self, challenge, response):
        if settings.RECAPTCHA_TEST_MODE:
            return True

        request = middleware.get_current_request()
        if request is not None and 'REMOTE_ADDR' in request.META.keys():
            ip = request.META['REMOTE_ADDR']
        else:
            ip = '127.0.0.1'
        return captcha.submit(challenge, response,
            settings.RECAPTCHA_PRIVATE_KEY, ip).is_valid

# vim:tabstop=4 shiftwidth=4 expandtab
