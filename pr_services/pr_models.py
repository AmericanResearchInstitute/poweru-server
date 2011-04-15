"""
data model for Power Reg 2

@author Michael Hrivnak <mhrivnak@americanri.com>
@author Andrew D. Ball <aball@americanri.com>
@author Randy Barlow <rbarlow@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import itertools
import logging
import os
import cPickle
import random
import re
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils.hashcompat import sha_constructor
import django.core.exceptions # for ValidationError
import django.db
import django.db.models.fields.related
import django.forms.util # for ValidationError
import exceptions
import facade
import pr_time
import storage
from fields import *

def queryset_empty(queryset):
    """
    Returns True if a Django queryset is empty, False otherwise.
    
    @param queryset a Django queryset
    
    This code is copied from the Django source code, from
    django/forms/models.py:255, svn revision 10283
    """
    
    # This cute trick with extra/values is the most efficient way to
    # tell if a particular query returns any results.
    if queryset.extra(select={'a': 1}).values('a').order_by():
        return False
    else:
        return True
    
def add_validation_error(validation_errors, attname, message):
    """
    Small helper method to help in accruing validation errors to the
    dictionary compiled by the PRModel.validate() method and validate()
    methods on descendants of PRModel.
    
    This quietly changes null or empty values of attname to "__SELF__"
    so that we don't end up trying to send dictionaries with empty strings
    as keys through AMF (see #2880).
    """
    
    # re #2880 (validation code tries to send dictionaries with empty string keys)
    # use a magic string rather than the empty string, so that we won't break
    # AMF
    if not attname:
        attname = "__SELF__"
    
    if not validation_errors.has_key(attname):
        validation_errors[attname] = list()
    validation_errors[attname].append(message)

def change_charfield_choices(model, attname, new_choices):
    """
    Change the choices available for a charfield.  Make sure
    that you make a copy of the previous choices list before
    replacing it.
    
    Example:
    
    import facade
    from pr_services.pr_models import change_charfield_choices
    STATUS_CHOICES = copy.deepcopy(facade.models.User.STATUS_CHOICES) 
    STATUS_CHOICES.extend([('funky', 'funky')])
    change_charfield_choices(facade.models.User, 'status', STATUS_CHOICES)
    """
    
    for field in model._meta.fields:
        if field.attname == attname:
            field._choices = new_choices
            break


class ModelDataValidationError(Exception):
    def __init__(self, validation_errors):
        """
        @param validation_errors
        @type validation_errors dict
        """
        
        self.validation_errors = validation_errors

    def __str__(self):
        return repr(self.validation_errors)
    
    def __unicode__(self):
        return unicode(self.validation_errors)

def cents_to_dollars_str(cents):
    """
    make a string representation of a dollar amount given
    a number of U.S. cents
    """

    s = '$' + str(cents)
    s = s[:-2] + '.' + s[-2:]
    return s

def alters_data(func):
    """
    Decorator used to tell Django that a method on a model shouldn't
    be called by templates because it alters data.  This is equivalent
    to setting the alters_data attribute of a function to True
    after defining the function, but I prefer to do this with a
    decorator.
    
    The Django community doesn't seem to want this, but I think
    it's cleaner, so I'm including it here.  See the following
    ticket in the Django trac instance for details:
        http://code.djangoproject.com/ticket/3009
    """
    
    func.alters_data = True
    return func


class Versionable(models.Model):
    """
    Use this mixin class for models which need to be versioned in a way that
    allows for version labels external to the system, comments for each version,
    and explicitly assigned sequence numbers.
    """
    #: used to explicitly order versions
    version_id = models.PositiveIntegerField(null=True)
    #: used to store any external identifiers for versions -- for example,
    #: a date, a Mercurial changeset id, "1.1-2", etc.
    version_label = models.CharField(max_length=255, blank=True, default='')
    #: optional comment to describe this version
    version_comment = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        abstract = True

    #: subclasses should define this class attribute as a tuple to indicate
    #: which field(s) should be considered unique for determining versions.
    version_fields = ()

    def validate(self, validation_errors=None):
        """
        Make sure that if the version fields are used then then they are
        unique when taken together.

        @param validation_errors dictionary of validation errors encountered so far,
            indexed by attribute name
        @type validation_errors dict or None
        """
        if validation_errors is None:
            validation_errors = dict()
        
        if self.version_id is not None and self.version_fields:
            unique_field_set = tuple(self.version_fields + ('version_id', 'version_label'))
            lookup_kw_args = {}
            for unique_field in unique_field_set:
                value = getattr(self, unique_field, None)
                lookup_kw_args[unique_field] = value

            possible_duplicates = self.__class__.objects.filter(**lookup_kw_args)
            # exclude the current object from the query if we're not
            # creating a new object
            if self.pk is not None:
                possible_duplicates = possible_duplicates.exclude(pk=self.pk)
            
            if not queryset_empty(possible_duplicates):
                add_validation_error(validation_errors, '__SELF__',
                    u'The following fields together are not unique: %s' %\
                     (unicode(unique_field_set)))
        
        return super(Versionable, self).validate(validation_errors)


class PRModel(models.Model):
    """
    PRModel - abstract base class for all models in the Power Reg system
    
    This provides a few different capabilities and behaviors from
    the standard Django model:
      (1) It has a delete method that changes django.db.models.ProtectedError
          to a subclass of PrException, and deletes any blame associated
          with the object.
      (2) It stores the actual type of each instance on creation, so
          that it's possible to get an instance of the most specific
          model class possible for a given instance (via the
          dynamic_cast method).
    """

    def _ensure_logger_availability(self):
        """
        Check to see if _logger is an instance of logging.Logger. If not, get one.
        """
        if not (hasattr(self, '_logger') and isinstance(self._logger, logging.Logger)):
            self._logger = logging.getLogger('%s.%s' % (self.__module__, self._meta.object_name))

    def _debug(self, message):
        """
        Write the message to log as level DEBUG only if debug is enabled in settings.

        @param  string message
        """
        if settings.DEBUG:
            self._ensure_logger_availability()
            self._logger.debug(message)

    #: the most specific type of this object (stored on its first save).
    #: This allows us to find out what type something "really" is with
    #: model inheritence and to convert to that type via the dynamic_cast method.
    #: The modified save method makes this work.
    final_type = PRForeignKey(ContentType)
    #: timestamp of object creation
    create_timestamp = models.DateTimeField(auto_now_add=True)
    #: timestamp of the last save operation
    save_timestamp = models.DateTimeField(auto_now=True)

    
    def truncate_charfields(self):
        """
        Silently truncate CharFields to their maximum lengths.
        
        I believe that this was happening on its own in Django 1.0, but
        does not happen automatically in Django 1.1.  This needs to
        be done before the validate() method is run, so that truncated
        values are validated rather than given values.
        """
        
        for field in self._meta.fields:
            if isinstance(field, models.CharField):
                value = getattr(self, field.attname)
                if value:
                    setattr(self, field.attname, value[0:field.max_length])
    
    def validate(self, validation_errors=None):
        """
        Nota bene:
        
        AMF can't handle dictionaries with empty strings as keys.  Before #2880
        was discovered, empty strings were used as fake attribute names and (real)
        dictionary keys to indicate errors which spanned more than one field.
        The magic name '__SELF__' should be used instead.  If you use the
        add_validation_error() function, this will happen automatically if
        you pass None or '' for the attribute name. 
        
        @param validation_errors dictionary of validation errors encountered so far,
            indexed by attribute name
        @type validation_errors dict or None
        """
        if validation_errors is None:
            validation_errors = dict()

        for field in self._meta.fields:
            if field.attname == 'final_type_id':
                continue
            # skip fields whose names end in 'ptr_id'
            if field.attname[-len('ptr_id'):] == 'ptr_id':
                continue
            
            current_value = getattr(self, field.attname, None)
            form_field = field.formfield()

            if hasattr(field, 'to_python'):
                try:
                    new_value = field.to_python(current_value)
                    setattr(self, field.attname, new_value)
                except django.core.exceptions.ValidationError, v:
                    validation_errors[field.attname] = [unicode(m) for m in v.messages]
                except Exception, e:
                    validation_errors[field.attname] = [unicode(e)]
            
            if form_field and current_value not in (None, ''):
                try:
                    form_field.clean(current_value)
                except django.core.exceptions.ValidationError, v:
                    validation_errors[field.attname] = [unicode(m) for m in v.messages]
                except django.forms.util.ValidationError, v:
                    validation_errors[field.attname] = [unicode(m) for m in v.messages]
            # don't check for uniqueness of the id field
            if field.attname == 'id':
                continue
            
            # test for uniqueness if this field has unique set to true
            # based on the Django BaseModelForm's validate_unique method
            if current_value not in (None, '') and field.unique == True:
                if isinstance(field, django.db.models.fields.related.OneToOneField):
                    attname = field.name
                else:
                    attname = field.attname
                                
                lookup_kw_args = {attname : field.to_python(current_value)}
                possible_duplicates = self.__class__.objects.filter(**lookup_kw_args)
                
                # exclude the current object from the query if we're not
                # creating a new object
                if self.id is not None:
                    possible_duplicates = possible_duplicates.exclude(id=self.id)
                    
                if not queryset_empty(possible_duplicates):
                    add_validation_error(validation_errors, attname,
                        u"Value is not unique.")
        
        unique_field_sets = []
        if self._meta.unique_together:
            # handle the shorthand ('field_name_1', field_name_2') for
            # (('field_name_1', 'field_name_1'),)
            if not (isinstance(self._meta.unique_together[0], list) or \
                isinstance(self._meta.unique_together[0], tuple)):
                unique_field_sets.append(self._meta.unique_together)
            else:
                for unique_field_set in self._meta.unique_together:
                    unique_field_sets.append(unique_field_set)
            for unique_field_set in unique_field_sets:                
                lookup_kw_args = dict()
                
                for unique_field in unique_field_set:
                    value = getattr(self, unique_field, None)
                    lookup_kw_args[unique_field] = value

                possible_duplicates = self.__class__.objects.filter(**lookup_kw_args)
                # exclude the current object from the query if we're not
                # creating a new object
                if self.pk is not None:
                    possible_duplicates = possible_duplicates.exclude(pk=self.pk)
                
                if not queryset_empty(possible_duplicates):
                    add_validation_error(validation_errors, '__SELF__',
                        u'The following fields together are not unique: %s' %\
                         (unicode(unique_field_set)))
        
        return validation_errors
                    
    @alters_data
    def delete(self):
        """
        Try to delete an object, ensuring that no other objects get
        deleted as a result. As of django 1.3, we rely on django to do the
        heavy lifting, and just modify the exception handing. This is
        also how blame gets cleaned up for objects with blame.
        """
        # If we're deleting an object that has Blame, we should delete the Blame as well
        if hasattr(self, 'blame') and (self.blame is not None):
            self.blame.delete()
        try:
            super(PRModel, self).delete()
        except django.db.models.ProtectedError, e:
            raise exceptions.CascadingDeleteException(*e.args)

    @alters_data
    def save(self, *args, **kw_args):
        """
        Modified save method that stores this object's type in its
        final_type attribute on its first invocation.
        
        This is based on the following thread in the django-users group:
        (subject: 'dynamic upcast', author of original message: 'dadapapa@gmail.com',
         url of archive:
         http://groups.google.com/group/django-users/browse_thread/thread/f4241bc16455f92d
        ) and the following article by Harold Fellermann:
          http://harold.teerun.de/article/dynamicdjango/
        """
        
        # silently truncate charfields
        self.truncate_charfields()
        
        # uncomment the next line to enable model data validation on every save
        validation_errors = self.validate()
        if len(validation_errors) > 0:
            logging.debug('validation errors: ' + str(validation_errors))
            raise ModelDataValidationError(validation_errors)
        
        # set the final type attribute only on its first save
        if not self.id:
            self.final_type = ContentType.objects.get_for_model(type(self))
        models.Model.save(self, *args, **kw_args)
        
    def downcast_completely(self):
        """
        Return an instance of this object, converted to the most specific model
        type possible.
        
        That is, if this is an instance of a subclass that uses multi-table
        inheritance, return an instance of that subclass.
        
        This is based on the following thread in the django-users group:
        (subject: 'dynamic upcast', author of original message: 'dadapapa@gmail.com',
         url of archive:
         http://groups.google.com/group/django-users/browse_thread/thread/f4241bc16455f92d
        ) and the following article by Harold Fellermann:
          http://harold.teerun.de/article/dynamicdjango/
        """
        
        # don't hit the database unless we need to
        if ContentType.objects.get_for_model(type(self)) != self.final_type:
            return self.final_type.get_object_for_this_type(id=self.id)
        else:
            return self
        
    class Meta:
        abstract = True


class OwnedPRModel(PRModel):
    #: The owner of this object
    owner = PRForeignKey('User', related_name='owned_%(class)ss', null=True)

    class Meta:
        abstract = True


class Note(OwnedPRModel):
    """
    Note
    
    A Note is used to store additional text on other objects
    """

    text = models.TextField()
    active = PRBooleanField(default = True)


class Organization(OwnedPRModel):
    """
    A Organization
    
    relationships:
     - users (0..* User to 0..* Organization)
     - roles (0..* OrgRole to 0..* Organization)
     - purchase_order (1 Organization to 0..* PurchaseOrder), attribute
       name is purchase_orders
    """

    name = models.CharField(max_length=127)
    department = models.CharField(max_length=127, null=True)
    notes = models.ManyToManyField(Note, related_name='organizations')
    address = PRForeignKey('Address', null=True, related_name='organizations')
    phone = models.CharField(max_length=31, null=True)
    email = models.EmailField()
    fax = models.CharField(max_length=31, null=True)
    active = PRBooleanField(default = True)
    description = models.TextField()
    parent = PRForeignKey('Organization', null=True, related_name='children')
    #: You can retrieve the photo itself by calling organization.photo, but more likely
    #: you want organization.photo.url to pass to the client.
    photo = models.ImageField(storage=storage.OrganizationPhotoStorage(), null=True, upload_to=settings.ORG_PHOTO_PATH)
    primary_contact_last_name = models.CharField(max_length=31)
    primary_contact_first_name = models.CharField(max_length=31)
    primary_contact_office_phone = models.CharField(max_length=31, null=True)
    primary_contact_cell_phone = models.CharField(max_length=31, null=True)
    primary_contact_other_phone = models.CharField(max_length=31, null=True)
    primary_contact_email = models.EmailField()
    url = models.URLField(null=True, verify_exists=False)
    roles = models.ManyToManyField('OrgRole', through='UserOrgRole', related_name='organizations')

    class Meta:
        unique_together = (('name', 'parent'),)

    def __unicode__(self):
        return self.name

    @property
    def ancestors(self):
        return self.get_ancestors()

    def get_ancestors(self, ancestors=None):
        """
        Return a list of primary keys including the parent and all other ancestors.
        This is useful for a client that wants to display the entire heirarchy. In
        one call, they can get a list of all ancestors and descendants, and in a
        second call retrieve the rest of those objects.
        """
        if ancestors is None:
            ancestors = []
        if self.parent is not None:
            ancestors.append(self.parent.id)
            self.parent.get_ancestors(ancestors)
        return ancestors

    @property
    def descendants(self):
        return self.get_descendants()

    def get_descendants(self, descendants=None):
        """
        Return a list of primary keys including the children and all other descendants.
        This is useful for a client that wants to display the entire heirarchy. In
        one call, they can get a list of all ancestors and descendants, and in a
        second call retrieve the rest of those objects.
        """
        if descendants is None:
            descendants = []
        if self.children.count() > 0:
            descendants.extend(self.children.values_list('id', flat=True))
            for child in self.children.all():
                child.get_descendants(descendants)
        return descendants


class OrgRole(PRModel):
    """
    A role that Users can have in an Oranization
    
    relationships:
     - users (0..* Users to 0..* OrgRoles)
     - orgs (0..* Orgs to 0..* OrgRoles)
    """
    name = models.CharField(max_length=255, unique=True)
    default = PRBooleanField(default=False)

    def __unicode__(self):
        return self.name


class UserOrgRole(OwnedPRModel):
    """
    Represents a relationship between a User and an Organization,
    characterized by an OrgRole.
    """
    # owner represents our user, and is inherited from OwnedPRModel
    organization = PRForeignKey('Organization', related_name='user_org_roles')
    role = PRForeignKey('OrgRole', related_name='user_org_roles')
    parent = PRForeignKey('self', null=True, related_name='children')
    
    def save(self, *args, **kwargs):
        try:
            self.role
        except OrgRole.DoesNotExist:
            self.role = OrgRole.objects.get(default=True)
        super(UserOrgRole, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('owner', 'organization', 'role')

    @property
    def role_name(self):
        return self.role.name

    @property
    def organization_name(self):
        return self.organization.name


class OrgEmailDomain(OwnedPRModel):
    """
    Mapping of email domain to organizations and roles used when creating new
    user accounts via self-registration.  If the role_to_assign is not set,
    the role attribute will return the default OrgRole.
    """

    email_domain = models.CharField(max_length=255)
    organization = PRForeignKey('Organization', related_name='org_email_domains')
    role = PRForeignKey('OrgRole', null=True, related_name='org_email_domains')

    class Meta:
        unique_together = ('email_domain', 'organization', 'role')

    @property
    def effective_role(self):
        return self.role or OrgRole.objects.get(default=True)

    @property
    def effective_role_name(self):
        return self.effective_role.name


class CredentialType(OwnedPRModel):
    """
    A CredentialType defines the prerequisites that must be completed in order
    for a User to earn a Credential. It represents an award, certificate or
    degree the User is trying to obtain.

    A CredentialType is a template for creating a Credential.  Every Credential
    is of a CredentialType, and can be thought of as a specific instantiation of
    a CredentialType associated with a User.
    """

    #: Unique name for this CredentialType.
    name = models.CharField(max_length=255, unique=True)
    #: Zero or more Notes related to this CredentialType.
    notes = models.ManyToManyField(Note, related_name='credential_types')
    #: Optional description of this CredentialType.
    description = models.TextField(null=True)
    required_achievements = models.ManyToManyField('Achievement', related_name='credential_types')
    #: These are other CredentialTypes that are prerequisites to being granted
    #: this one.  Currently all of them must be satisfied, but we could have a
    #: more complicated rule system in the future.
    prerequisite_credential_types = models.ManyToManyField('self',
        symmetrical=False, related_name='requisite_credential_types')

    def completed(self, user):
        """
        Return a boolean indicating whether the given User meets all
        requirements to be granted a Credential of this type.
        """

        # Check that the User has been granted Credentials for all of the
        # prerequisite_credential_types.
        for required_credential_type in self.prerequisite_credential_types.all():
            if not required_credential_type.credentials.filter(
                    user__id=user.id, status='granted').count():
                return False

        # Check that the user has completed all required Achievements
        user_achievement_awards = user.achievement_awards.all()
        user_achievement_award_ids = [award.achievement.id for award in user_achievement_awards]
        for achievement_id in self.required_achievements.values_list('id', flat=True):
            if achievement_id not in user_achievement_award_ids:
                return False

        return True

    def __unicode__(self):
        return self.name


class Credential(OwnedPRModel):
    """
    A Credential is the association of a CredentialType with a User.
    """

    notes = models.ManyToManyField(Note, related_name='credentials')
    #: store the type of the Credential
    credential_type = PRForeignKey(CredentialType, null=False, related_name='credentials')
    #: the authority who granted the Credential
    authority = models.CharField(max_length=255, null=True)
    #: the ID of the Credential given by the authority
    serial_number = models.CharField(max_length=255, null=True)
    #: the date the User was assigned the burden of attempting to achieve this
    #: Credential.  It is the same time as the creation event of the Credential.
    date_assigned = models.DateTimeField(null=False, auto_now=True)
    #: the date the Credential status was set to 'granted'
    date_granted = models.DateTimeField(null=True)
    #: the optional expiration date of the Credential
    date_expires = models.DateTimeField(null=True)
    #: the date that the User began working on completing the Credential
    date_started = models.DateTimeField(null=True)
    #: the User whose Credential it is
    user = PRForeignKey('User', null=False, related_name='credentials')
    STATUS_CHOICES = (
        ('granted', 'granted'),
        ('revoked', 'revoked'),
        ('pending', 'pending'),
        ('expired', 'expired'),
    )
    #: the Credential has a status to indicate whether the User has yet achieved the Credential
    #: or not.  'granted' indicates that the User has achieved the Credential. 'revoked',
    #: 'pending', or 'expired' indicates that they have not.  'pending' means that the User is
    #: in the process of attempting to achieve the Credential, and is how we know what Tasks to
    #: assign to the User
    status = models.CharField(max_length=8, null=False, choices=STATUS_CHOICES,
        default='pending')

    def __unicode__(self):
        return u'Credential, id=%d' % (self.id)

    def check_requirements_for_completion(self):
        """
        Check that this Credential's User meets all requirements to be granted
        the Credential, and if so, mark it as granted.
        """

        credential_type = self.credential_type.downcast_completely()
        if credential_type.completed(self.user):
            self.downcast_completely().mark_granted()

    def mark_granted(self):
        """
        Mark the Credential as granted and set the completion date.
        """

        self.status = 'granted'
        self.date_granted = datetime.utcnow()
        self.save()


class Achievement(OwnedPRModel):
    """
    Awarded to a user upon completion of an assignment, or upon having attained
    some collection of other achievements. It is possible that several tasks
    independently yield the same achievement.
    """

    description = models.TextField()
    name = models.CharField(max_length=255)
    organization = PRForeignKey('Organization', related_name='achievements', null=True)
    users = models.ManyToManyField('User', through='AchievementAward', related_name='achievements')
    # Getting all of these achievements means you will automatically be given this achievement too.
    component_achievements = models.ManyToManyField('Achievement', related_name='yielded_achievements')


class AchievementAward(PRModel):
    """
    represents that a user was awarded an achievement.  If completion of an
    Assignment resulted in earning it, a reference to that Assignment is
    stored.
    """

    achievement = PRForeignKey('Achievement', related_name='achievement_awards')
    user = PRForeignKey('User', related_name='achievement_awards')
    # If the completion of an Assignment was the tipping point that resulted in
    # the awarding of this Achievement, we store that relationship here.
    assignment = PRForeignKey('Assignment', related_name='achievement_awards', null=True)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Looks for credentials that can be granted if that time has come.
        """

        new_award = self.pk is None

        super(AchievementAward, self).save(*args, **kwargs)

        if new_award:
            candidate_credential_types = self.achievement.credential_types.all()
            pending_credential_types = CredentialType.objects.filter(credentials__user__id=self.user.id,
                credentials__status='pending')
            for credential_type in candidate_credential_types:
                if credential_type.completed(self.user):
                    if credential_type in pending_credential_types:
                        credential = Credential.objects.get(user=self.user, credential_type=credential_type)
                    else:
                        credential = Credential.objects.create(user=self.user, credential_type=credential_type)
                    credential.mark_granted()


class Task(OwnedPRModel, Versionable):
    """The smallest unit of work that a User can complete.

    Completing a task may give a user one or more achievements. A task may be
    to show up to a session, pass an exam, fill out a survey, etc. A task may
    be related to any number of achievements that are prerequisites. For
    example, before taking a survey, a user must show up for two session. Each
    of those sessions gives the user an achievement, and possessing those
    achievements entitles them to take the survey.

    """
    users = models.ManyToManyField('User', through='Assignment', related_name='tasks')
    description = models.TextField()
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=191, null=True)
    #: These are the Tasks that must be completed before this Task can be attempted
    prerequisite_tasks = models.ManyToManyField('self', symmetrical=False,
        related_name='yielded_tasks')
    #: These are the Achievements that must be completed before this Task can be attempted
    prerequisite_achievements = models.ManyToManyField('Achievement',
        related_name='yielded_tasks')
    #: Whether this Task is publicly viewable or not
    public = PRBooleanField(default=False)
    min = models.PositiveIntegerField(default=0)
    # maximum Assignments -- None means no maximum
    max = models.PositiveIntegerField(null=True)
    # Should the system prevent a user from having more than one assignment to this?
    prevent_duplicate_assignments = PRBooleanField(default=False)
    # achievements that get awarded upon completion of this task
    achievements = models.ManyToManyField('Achievement', related_name='tasks')

    @property
    def remaining_capacity(self):
        if self.max is None:
            return 10000
        else:
            return max(0, self.max - self.confirmed_assignments)

    @property
    def confirmed_assignments(self):
        """
        number of assignments that count toward capacity
        """

        statuses = ['assigned', 'pending', 'late', 'completed']
        return self.assignments.filter(status__in=statuses).count()

    def completed(self, user):
        """
        Returns True iff the User has completed an Assignment for this Task.

        @param user The User in question
        @type user  User
        @return     True if the User has completed an Assignment for this Task
        """
        # If there aren't any completed Assignments for this Task, return False
        if self.assignments.filter(user__id=user.id, status='completed').count() > 0:
            return True
        return False

    def prerequisites_met(self, user):
        """
        Returns True iff the User has satisfied all the prerequisites for this Task.

        @param user The User who we are checking the prerequisites for
        @type user  User
        @return     True iff the User has satisfied all the prerequisites for this Task.
        """
        # Make sure the User has at least one completed Assignment for each prerequisite Task
        for prerequisite_task in self.prerequisite_tasks.all():
            prerequisite_task = prerequisite_task.downcast_completely()
            if not prerequisite_task.completed(user):
                return False
        # We've checked all the prerequisite Tasks, and haven't found the User to be
        # ineligible, so let's return True
        return True

    def save(self, *args, **kwargs):
        # Create a name based on the title if present, otherwise use the content
        # type and primary key to generate the name.
        update_name_with_pk = False
        if self.pk is None and not self.name:
            if self.title:
                self.name = re.sub(r'\W', '_', self.title.lower())
            else:
                self.name = str(id(self)) # Temporary name so validation will work.
                update_name_with_pk = True
        super(Task, self).save(*args, **kwargs)
        # Now update the name since we know the PK.
        if update_name_with_pk:
            self.name = '%s_%d' % (self.final_type.name, self.pk)
            self.save()

    def __unicode__(self):
        return u'(Task %s, id=%d)' % (self.name, self.id if self.id else -1)


class Curriculum(PRModel):
    name = models.CharField(max_length=255)
    organization = PRForeignKey('Organization', null=True, related_name='curriculums')
    achievements = models.ManyToManyField('Achievement', related_name='curriculums')
    tasks = models.ManyToManyField('Task', through='CurriculumTaskAssociation', related_name='curriculums')

    
class CurriculumTaskAssociation(PRModel):
    """
    Collection of tasks and achievements that must be completed. Also has a name
    and organization. Each association with a Task may optionally specify a
    TaskBundle, and the association must include a display sequence value.

    adding Tasks to a Curriculum means "Learners must complete this Task during
    their CurriculumEnrollment no matter how many times they may have completed
    it in the past".

    adding Achievements to a Curriculum means "Make sure the Learner has learned
    this stuff at some point, and it is ok if they learned it in the past."
    """

    curriculum = PRForeignKey('Curriculum', related_name='curriculum_task_associations')
    task = PRForeignKey('Task', related_name='curriculum_task_associations')
    task_bundle = PRForeignKey('TaskBundle', null=True, related_name='curriculum_task_associations')
    # order in which to present this task to users (relative to the other
    # tasks under the same Curriculum).  The constraints on this are
    # intentionally lax.  Equal values of presentation_order with the same
    # curriculum but different tasks are permitted, and they signify that
    # the corresponding two tasks can go in any order relative to each
    # other.  However, lesser values for presentation_order mean that their
    # corresponding tasks are presented first.  For example,
    # 0 1 1 2 3 4 5 5 5 might be the presentation_order values for a correctly
    # ordered set of tasks.
    presentation_order = models.PositiveSmallIntegerField(default=0)
    continue_automatically = PRBooleanField(default=False)
    # How many days after the start of the curriculum_enrollment must the user
    # wait to attempt this task?
    days_before_start = models.PositiveSmallIntegerField(default=0)
    # How many days does the user have to complete this task? This is how an
    # assignment's due date is set. If this is 0, the due date will default to
    # the curriculum_enrollment's end date
    days_to_complete = models.PositiveSmallIntegerField(default=0)


class CurriculumEnrollment(PRModel):
    """
    Associates any number of users with a curriculum, having a start and end
    date. All Assignments generated as a result of this object are also
    associated directly. This is how progress will be measured.
    """

    curriculum = PRForeignKey('Curriculum', related_name='curriculum_enrollments')
    users = models.ManyToManyField('User', through='CurriculumEnrollmentUserAssociation', related_name='curriculum_enrollments')
    start = models.DateField()
    end = models.DateField()

    @property
    def user_completion_statuses(self):
        """
        get the completion statuses for all users associated with this
        CurriculumEnrollment

        This probably won't perform well if there is a large number of users
        and assignments.

        :returns    dictionary of booleans, indexed by user PK. True iff the
                    user has completed this CurriculumEnrollment, else False
        """

        assignments = self.assignments.all()
        # group by user
        sorted_assignments = {}
        for assignment in assignments:
            if assignment.user.id in sorted_assignments:
                sorted_assignments[assignment.user.id].append(assignment)
            else:
                sorted_assignments[assignment.user.id] = [assignment]
        ret = {}
        for user in self.users.all():
            ret[user.id] = self.get_user_completion_status(user, sorted_assignments[user.id])
        return ret

    @property
    def number_of_tasks(self):
        """ this exists just to cache the value """

        if not hasattr(self, '_number_of_tasks') or self._number_of_tasks is None:
            self._number_of_tasks = self.curriculum.tasks.all().count()
        return self._number_of_tasks

    def get_user_completion_status(self, user, assignments=None):
        """
        get the completion status for a user.

        :param user:        user object
        :param assignments: optional list of assignments. This is here only to
                            allow for optimization when this method will be
                            called many times in a row

        :returns            True iff the user has completed this
                            CurriculumEnrollment, else False
        """

        if assignments is None:
            assignments = self.assignments.filter(user__id=user.id)
        ret = True
        if len(assignments) == 0:
            ret = False
        elif len(assignments) != self.number_of_tasks:
            ret = False
        else:
            for assignment in assignments:
                if assignment.status != 'completed':
                    ret = False
                    break

        return ret


class CurriculumEnrollmentUserAssociation(PRModel):
    """
    This class exists only so we can create assignments automatically at the time
    of enrollment. We do that by overriding the save() method
    """
    curriculum_enrollment = PRForeignKey('CurriculumEnrollment', related_name='curriculum_enrollment_user_associations')
    user = PRForeignKey('User', related_name='curriculum_enrollment_user_associations')

    def save(self, *args, **kwargs):
        ret = super(CurriculumEnrollmentUserAssociation, self).save(*args, **kwargs)
        
        # make assignments automatically if they don't already exist
        for task in self.curriculum_enrollment.curriculum.tasks.all():
            assignment, created = Assignment.objects.get_or_create(user=self.user, task=task, curriculum_enrollment=self.curriculum_enrollment)
            if created:
                # set dates
                cta = CurriculumTaskAssociation.objects.get(curriculum=self.curriculum_enrollment.curriculum, task=task)
                assignment.effective_date_assigned = self.curriculum_enrollment.start + timedelta(days=cta.days_before_start)
                if cta.days_to_complete > 0:
                    assignment.due_date = assignment.effective_date_assigned + timedelta(days=cta.days_to_complete)
                else:
                    assignment.due_date = self.curriculum_enrollment.end
                assignment.save()
        return ret
        

class Assignment(PRModel):
    """
    An Assignment is a relationship between a User and a Task. The User makes
    one or more AssignmentAttempts. If one is successful, this Assignment
    is marked as completed, and Credentials may be awarded.
    """

    user = PRForeignKey('User', related_name='assignments')
    STATUS_CHOICES = (
        ('assigned', 'assigned'), # user has not begun the assignment
        ('canceled', 'canceled'), # the assignment has been canceled
        ('completed', 'completed'), # user has completed the assignment
        ('late', 'late'), # user did not complete assignment before deadline
        ('no-show', 'no-show'),
        ('pending', 'pending'), # user has begun but not completed the assignment
        ('unpaid', 'unpaid'), # the assignment requires payment which has not been recorded
        ('wait-listed', 'wait-listed'),
        ('withdrawn', 'withdrawn'), # user was withdrawn from assignment
    )
    status = models.CharField(max_length=16, null=False, choices=STATUS_CHOICES, default='assigned',
        db_index=True)
    #: the date the User completed the Assignment
    date_completed = models.DateTimeField(null=True)
    #: the date the the User began the Assignment
    date_started = models.DateTimeField(null=True)
    #: the date that the Assignment is due (null means no hard due date)
    due_date = models.DateTimeField(null=True)
    #: the effective_date_assigned is the date that is planned for the User to begin attempting
    #: the Assignment
    effective_date_assigned = models.DateTimeField(null=True)
    #: the Task that this Assignment is an instance of
    task = PRForeignKey(Task, related_name='assignments')
    #: the authority who granted the Assignment as completed
    authority = models.CharField(max_length=255, null=True)
    #: the ID of the assginment given by the authority
    serial_number = models.CharField(max_length=255, null=True)
    
    #: whether the assignment confirmation email has been sent
    #: (which is typically sent around the effective_date_assigned)
    sent_confirmation = PRBooleanField(default=False)
    #: whether a late notice has been sent
    sent_late_notice = PRBooleanField(default=False)
    #: whether a reminder has been sent
    sent_reminder = PRBooleanField(default=False)
    # If this has been paid for, the following relationship should be defined.
    product_claim = PRForeignKey('ProductClaim', null=True, related_name='assignments')
    blame = PRForeignKey('Blame', null=True, related_name='assignments')
    curriculum_enrollment = PRForeignKey('CurriculumEnrollment', null=True, related_name='assignments')
    #: whether a "pre-reminder" has been sent
    sent_pre_reminder = PRBooleanField(default=False)
    
    @property
    def task_content_type(self):
        return self.task.final_type.app_label + '.' + self.task.final_type.name

    @property
    def prerequisites_met(self):
        """Return True iff all prerequiseties have been met"""

        for task in self.task.prerequisite_tasks.all():
            if task.assignments.filter(status='completed', user=self.user).count() == 0:
                return False
        return True

    def mark_completed(self):
        """
        This method is a helper method that is used to mark this Assignment as
        completed.  It sets the completion date to now, and the status to
        'completed'.  It also notifies any Credentials that are waiting on the
        task to be completed, in case the User is eligible for any Credentials.
        """

        self.status = 'completed'
        self.date_completed = datetime.utcnow()
        # We need to call the super class save here so that the change of
        # 'completed' will be detected in the Credential checks.
        super(Assignment, self).save()

        # Look for any Achievements that should be awarded
        for achievement in self.task.achievements.all():
            AchievementAward.objects.create(user=self.user, achievement=achievement,
                assignment=self)

    @property
    def payment_required(self):
        """
        Returns True if this Assignment requires payment before it can be 
        attempted.  This does not consider the current status.  If this Assignment
        has a status other than 'unpaid', the user may safely disregart this
        value.
        """
        if self.task.task_fees.count():
            return not (isinstance(self.product_claim, ProductClaim) and self.product_claim.is_paid)
        else:
            return False

    def save(self, *args, **kwargs):
        """
        Makes sure that the mark_completed() method gets run if the status has changed
        to 'completed'.  Also checks the payment information for this assignment and
        updates the status accordingly.
        """

        if self.pk is None:
            # The first time the object is saved, see if it requires payment.
            # By only checking the first time, we allow an admin to override
            # this and simply change the 'unpaid' status to something else
            if self.status != 'wait-listed' and self.payment_required:
                self.status = 'unpaid'
        else:
            old_status = self.__class__.objects.get(pk=self.pk).status
            if old_status != 'completed' and self.status == 'completed':
                self.mark_completed()
            # If this was just paid for, let's update the status
            elif old_status == 'unpaid':
                if not self.payment_required:
                    self.status = 'assigned'

        super(Assignment, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'(Assignment for %s, id=%d, user=%s)' % \
            (repr(self.task), self.id, repr(self.user))


class AssignmentAttempt(OwnedPRModel):
    """
    An AssignmentAttempt is an instance of a User's attempt of an assigned Task
    """

    assignment = PRForeignKey('Assignment', related_name='assignment_attempts')
    #: the date the User completed the Assignment
    #: assume the attempt it not complete unless this is non-null
    date_completed = models.DateTimeField(null=True)
    #: the date the the User began the Assignment
    date_started = models.DateTimeField()

    def save(self, *args, **kwargs):
        """
        If date_started hasn't been specified and this is a new object, set
        it to now.

        Note that subclasses are still responsible for deciding when they can
        be marked as completed, and for then setting date_completed to a completion
        timestamp. This is because different types of AssignmentAttempts may have
        different ways of defining successful completion.
        """

        # Set default attributes on creation.
        if self.id is None:
            if self.date_started is None:
                self.date_started = datetime.utcnow()
        super(AssignmentAttempt, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'(AssignmentAttempt for (%s), id=%d)' % \
            (repr(self.assignment), self.id)


class TaskBundle(PRModel):
    """
    A collection of Tasks with an organization and an optional name. This is
    only used for the purposes of automatic assignments in a
    CurriculumEnrollment.
    """

    name = models.CharField(max_length=255)
    description = models.TextField()
    organization = PRForeignKey('Organization', related_name='task_bundles', null=True)
    tasks = models.ManyToManyField('Task', through='TaskBundleTaskAssociation',
        related_name='task_bundles')

    def __unicode__(self):
        return u'(TaskBundle %s, id=%d)' % (self.name, self.id)


class TaskBundleTaskAssociation(PRModel):
    """
    Association class for the many-to-many relationship between TaskBundle
    and Task.  Provides the presentation order of the Tasks associated with a
    given TaskBundle.
    """

    task_bundle = PRForeignKey('TaskBundle', null=False,
        related_name='task_bundle_task_associations')
    task = PRForeignKey('Task', related_name='task_bundle_task_associations', null=False)

    # order in which to present this task to users (relative to the other
    # tasks under the same TaskBundle).  The constraints on this are
    # intentionally lax.  Equal values of presentation_order with the same
    # task bundle but different tasks are permitted, and they signify that
    # the corresponding two tasks can go in any order relative to each
    # other.  However, lesser values for presentation_order mean that their
    # corresponding tasks are presented first.  For example,
    # 0 1 1 2 3 4 5 5 5 might the presentation_order values for a correctly
    # order set of tasks associated with a task bundle.
    presentation_order = models.PositiveIntegerField(null=False, default=0)

    # whether to automatically proceed to the next task on completion
    # This was needed for QinetiQ, where it was expected that an exam be
    # shown to the user immediately after completing a Sco.
    continue_automatically = PRBooleanField(default=False)

    def __unicode__(self):
        return (u'TaskBundleTaskAssociation: task bundle [%s] task [%s]' %
            (unicode(self.task_bundle), unicode(self.task)))


class ProductLine(OwnedPRModel):
    """
    A ProductLine is a collection of classes
    
    relationships:
     - session_template (1 SessionTemplate to 0..1 ProductLine)
    """

    name = models.CharField(max_length=255, unique=True)
    notes = models.ManyToManyField(Note, related_name = 'product_lines')
    managers = models.ManyToManyField('User', related_name='product_lines_managed')
    #: define the instructor managers here.  The related_name could probably be improved.
    instructor_managers = models.ManyToManyField('User',
            related_name='product_lines_instructor_manager_for')
    #: define the instructors here
    instructors = models.ManyToManyField('User', related_name='product_lines_instructor_for')
    active = PRBooleanField(default = True)

    def __unicode__(self):
        return self.name


class Region(OwnedPRModel):
    """
    A geographic region in which Venues exist
    
    relationships:
     - venue (1 Venue to 0..1 region)
     - session (1 Session to 0..1 region)
    """
    name = models.CharField(max_length=255, unique=True)
    notes = models.ManyToManyField(Note, related_name = 'regions')
    active = PRBooleanField(default = True)

    def __str__(self):
        return self.name
    def __unicode__(self):
        return u'%s' % (self.name)


class Resource(OwnedPRModel):
    """
    Items that can be assigned or required by Sessions
    This has a many-to-many relationship with the ResourceType class,
    the Session class, and the User class.
    The field names for collections of related objects of these classes
    are Resources, Sessions, and Users, respectively.
    
    from the glossary:
      Resource: any kind of item that can be listed as an Session/SessionTemplate
    requirement that is not a User, Venue, or a date/time element. End
    users are able to define Resources and associate any number of
    ResourceTypes to them. 
    """

    name = models.CharField(max_length=255, unique=True)
    notes = models.ManyToManyField(Note, related_name = 'resources')
    active = PRBooleanField(default = True)
    # many-to-many relationship with ResourceType gives us a resource_types field
    # many-to-many relationship with Session gives us a sessions field
    def __str__(self):
        return self.name
    def __unicode__(self):
        return u'%s' % (self.name)


class Group(OwnedPRModel):
    """
    A Group is a set of Users
    """

    name = models.CharField(max_length=255, unique=True)
    notes = models.ManyToManyField(Note, related_name = 'groups')
    # many-to-many relationship with User gives us a users field
    # Group managers can add/remove Users and fun stuff like that
    managers = models.ManyToManyField('User', related_name = 'groups_managed')
    active = PRBooleanField(default = True)
    # if default=True, then every new user will be added to this group
    default = PRBooleanField(default = False)

    def __str__(self):
        return '%s' % (self.name)
    def __unicode__(self):
        return unicode(str(self))

    class Meta:
        ordering = ('name',)


class Role(OwnedPRModel):
    """
    A Role is a collection of ACLs with the rules that are necessary to decide if they should be applied to a request.
    """
    #: The name of the Role
    name = models.CharField(max_length=255, unique=True)
    notes = models.ManyToManyField(Note, related_name = 'roles')

    def __str__(self):
        return 'Role: %s'%self.name

    def __unicode__(self):
        return unicode(str(self))


class ACL(OwnedPRModel):
    """
    An ACL is a collection of rules and access control lists.
    """
    #: list of methods that must ALL return True for the acl to be granted
    ac_check_methods = models.ManyToManyField('ACCheckMethod', through='ACMethodCall', related_name='acls')
    #: We use the Python pickle module to store the acl.
    #: The acl is a dictionary of dictionaries.  The outer keys are
    #: object types, and they point to dictionaries that have the
    #: keys 'c', 'r', 'u', and 'd'.  'c' and 'd' point to boolean
    #: values, indicating whether or not the User can create and
    #: delete objects of the specified type, respectively.  'r' and
    #: 'u' point to attribute lists, indicating which attributes the
    #: User has access to when reading and updating.
    #:
    #: For example:
    #:
    #: acl = {
    #:   'User' : {
    #:       'c' : True,
    #:       'r' : ['username', 'first_name', 'last_name'],
    #:       'u' : [],
    #:       'd' : False,
    #:   },
    #: }
    acl = models.TextField() 
    #: The arbitrary_perm_list is a pickled list of strings that
    #: represent some arbitrary permission names that can be
    #: granted.  The vast majority of possible permissions are
    #: granted through the acl, but there are a few special cases
    #: that this arbitrary list is used for, such as the ability to
    #: view reports.
    arbitrary_perm_list = models.TextField()
    role = PRForeignKey(Role, related_name='acls')

    def merge_updates(self, acl_updates):
        """
        Sometimes we need to extend an existing ACL, for example when we have a variant of pr_services.
        In that case, it is useful to extend ACLs when we add custom attributes to models. This method
        exists to make that process easy.

        Simply pass in an ACL that only defines those parameters you want updated. For 'r' and 'u',
        you cannot currently take away permission.  You can only add.

        Example:

        {
            'User' : {
                'r' : ['annual_beer_consumption'],
            },
            'Beer' : {
                'c' : True,
                'r' : ['name', 'brewery', 'style', 'IBU',]
                'u' : [],
                'd' : False,
            }
        }

        This example does two things:
        1) it updates the ACL so that the attribute 'annual_beer_consumption' of the User model can be read.
           In this case, define only those permissions that you want to modify. It is ok to leave out 'cud'.
        2) it adds an ACL for an entirely new model, 'Beer'. In this case, all four of 'crud' are required.

        @param acl_updates  dict containing updates to the ACL as described above
        @type  acl_updates  dict
        """
        acl_dict = cPickle.loads(str(self.acl))

        for model_acl in acl_updates:
            model_dict = acl_updates[model_acl]
            if model_acl in acl_dict:
                if 'c' in model_dict:
                    acl_dict[model_acl]['c'] = model_dict['c']
                if 'r' in model_dict:
                    acl_dict[model_acl]['r'].extend(model_dict['r'])
                if 'u' in model_dict:
                    acl_dict[model_acl]['u'].extend(model_dict['u'])
                if 'd' in model_dict:
                    acl_dict[model_acl]['d'] = model_dict['d']
            else:
                if acl_updates[model_acl].keys() != ['c','r','u','d']:
                    raise exceptions.InvalidInputException('new ACL for model %s must have all four CRUD components' % (model_acl))
                acl_dict[model_acl] = model_dict

        self.acl = cPickle.dumps(acl_dict)
        self.save()


class ACCheckMethod(OwnedPRModel):
    """
    "AC" is for "Access Control".  The check_method model is used to store
    information in the database about available access control methods that the
    admin can use to create new Roles.

    These methods each return a boolean value, and they can be used to define
    Roles in the system.
    """

    #: the name of the method in the authorizer class to be called
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField()
    title = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return '%s' % (self.name)
    def __unicode__(self):
        return unicode(str(self))


class ACMethodCall(OwnedPRModel):
    """
    AC is for "Access Control". The ACMethodCall model describes a
    method call that should return True or False to indicate whether
    an actor is acting in a particular Role or not.
    
    This is a through table for a many-to-many relationship between
    the 'ACCheckMethod' and 'Role' models.  Its primary purpose
    is to include additional information to pass to the boolean
    method indicated (the 'ACCheckMethod') that is specific
    to a given Role, such as the Group id for a Role that has
    membership defined by membership in a given Group.

    The ac_check_parameters is an optional list of additional
    arguments to be passed to the boolean method to perform the check,
    such as the Group id of a Group for a Group membership test, encoded
    as a pickled dictionary mapping argument names to values.

    A Role can have one or more ACMethodCalls defined, each with
    their own optional list of parameters. These methods must all return
    True for the actor to be granted access under that Role.
    """

    acl = PRForeignKey(ACL, related_name='ac_method_calls')
    ac_check_method = PRForeignKey(ACCheckMethod, related_name='ac_method_calls')
    #: a pickled dictionary of method parameters, stored as a string
    ac_check_parameters = models.TextField()


class Address(OwnedPRModel):
    """
    These objects should only be associated with one other object.
    
    relationships:
      - user (1 User to 0..1 Address) [shipping_address]
      - user (1 User to 0..1 Address) [billing_address]
      - venue (1 Venue to 0..1 Address)
    """

    #: country (two letter ISO code, e.g. us, fi, de, jp, cn)
    country = models.CharField(max_length=2)
    #: state in the US
    region = models.CharField(max_length=31, null=True, blank=True, default='')
    #: city in the US
    locality = models.CharField(max_length=31, null=True, blank=True, default='')
    #: zip code in the US
    postal_code = models.CharField(max_length=16, null=True, blank=True, default='')
    #: all Address lines above the locality but below a person's name
    label = models.CharField(max_length=255)
    active = PRBooleanField(default = True)

    def __unicode__(self):
        return u'%s\n%s\n%s\n%s\n%s' % (self.label, self.locality, self.region, self.postal_code,
                                  self.country)

class Domain(PRModel):
    authentication_ip = models.IPAddressField(null=True)
    authentication_password_hash = models.CharField(max_length=128)
    name = models.CharField(max_length=255, unique=True, null=False)
    PASSWORD_HASH_TYPE_CHOICES = (
        ('SHA-1', 'SHA-1'),
        ('SHA-512', 'SHA-512'),
    )
    password_hash_type = models.CharField(max_length=8, choices=PASSWORD_HASH_TYPE_CHOICES,
            default='SHA-512')
    
    
class DomainAffiliation(PRModel):
    default = PRBooleanField(default=False)
    domain = PRForeignKey('Domain', related_name='domain_affiliations')
    may_log_me_in = PRBooleanField(default=False)
    #: cryptographic hash of the User's password
    # leave enough room for a SHA-512 hash in hex
    password_hash = models.CharField(max_length=128)
    #: type of cryptographic hash used for the password_hash field
    #: currently only 'SHA-1' is supported
    PASSWORD_HASH_TYPE_CHOICES = (
        ('SHA-1', 'SHA-1'),
        ('SHA-512', 'SHA-512'),
    )
    password_hash_type = models.CharField(max_length=8, choices=PASSWORD_HASH_TYPE_CHOICES,
            default='SHA-512')
    # Store the user's password salt.  The hash is made from the concatenation of the user's password and their salt
    password_salt = models.CharField(max_length=8, null=True)
    user = PRForeignKey('User', related_name='domain_affiliations')
    username = models.CharField(max_length=31, blank=False, db_index=True)
    #: these are characters that are not permitted for the username field
    USERNAME_ILLEGAL_CHARACTERS = '!$%^&;"+=/?\|()[]{}`~\''
    
    class Meta:
        unique_together = (('username', 'domain'),)

    def validate(self, validation_errors=None):
        """
        Let's validate the username to ensure that it meets requirements.  Currently, the only requirements are that the username not be empty, and not be the same as another
        username in the system.
        """
        if validation_errors is None:
            validation_errors = dict()
        
        validation_errors = PRModel.validate(self, validation_errors)

        try:
            potential_duplicate = self.__class__.objects.get(username=self.username, domain=self.domain)
            if self.id is None:
                add_validation_error(validation_errors, 'username', u"The username %s is already in use."%self.username)
        except self.__class__.DoesNotExist:
            pass
        
        if len(self.username) < 1:
            add_validation_error(validation_errors, 'username', u"Username must be at least one character long.")
        
        if self.username.strip() != self.username:
            add_validation_error(validation_errors, 'username', u"Usernames may not begin or end in whitespace.")

        if self.domain.name == 'local':
            # Check for additional illegal characters
            for c in self.username:
                if (c in self.__class__.USERNAME_ILLEGAL_CHARACTERS):
                    add_validation_error(validation_errors, 'username', u"You have used an invalid character in the username field.  We do not allow the following characters: " +\
                        self.__class__.USERNAME_ILLEGAL_CHARACTERS)

        return validation_errors
    

class User(OwnedPRModel):
    """Our representation of a user, which is currently distinct from django.contrib.auth.User.

    At some point we may make our User class compatible with django.contrib.auth's
    version, but that would require some additional features, including:
      1. less restrictive usernames (we have to allow spaces at the very least)
      2. domains/realms

    """
    #: A URL for the User
    url = models.URLField(null=True, verify_exists=False)
    #: the User's domain
    domains = models.ManyToManyField('Domain', through='DomainAffiliation', related_name='users')
    title = models.CharField(max_length = 15, null=True)
    #: the User's last name / surname
    last_name = models.CharField(max_length=31)
    #: the User's middle name
    middle_name = models.CharField(max_length=31, default='')
    #: the User's first name / given name / Christian name
    first_name = models.CharField(max_length=31)
    #: the User's name suffix
    name_suffix = models.CharField(max_length=15, null=True)

    def get_full_name(self):
        """ returns a formatted full name """
        full_name = u''
        if self.title:
            full_name += self.title + ' '
        if self.first_name:
            full_name += self.first_name + ' '
        if self.middle_name:
            full_name += self.middle_name + ' '
        if self.last_name:
            full_name += self.last_name
        if self.name_suffix:
            full_name += ', ' + self.name_suffix
        return full_name.strip()

    #: formatted full name derived attribute
    full_name = property(get_full_name)

    #: an associated primary Address
    shipping_address = PRForeignKey(Address, null=True, related_name='users_shipping')
    billing_address = PRForeignKey(Address, null=True, related_name='users_billing')
    organizations = models.ManyToManyField('Organization', through='UserOrgRole', related_name='users')
    roles = models.ManyToManyField('OrgRole', through='UserOrgRole', related_name='users')
    #: store phone numbers as strings to make
    #: storing international numbers easy.  we can
    #: add validation or more room as needed.
    phone = models.CharField(max_length=31, null=True)
    phone2 = models.CharField(max_length=31, null=True)
    phone3 = models.CharField(max_length=31, null=True)
    email = models.EmailField()
    email2 = models.EmailField(null=True)
    paypal_address = models.EmailField(null=True)
    enable_paypal = PRBooleanField(default=False)
    STATUS_CHOICES = [
        ('active', 'active'),
        ('inactive', 'inactive'),
        ('pending', 'pending'),
        ('qualified', 'qualified'),
        ('suspended', 'suspended'),
        ('training', 'training'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, null=True)
    groups = models.ManyToManyField(Group, related_name = 'users')
    notes = models.ManyToManyField(Note, related_name = 'users')
    color_code = models.CharField(max_length = 31, null = True)
    blame = PRForeignKey('Blame', null=True, related_name = 'created_users')
    biography = models.TextField(null=True)
    #: You can retrieve the photo itself by calling user.photo, but more likely
    #: you want user.photo.url to pass to the client.
    photo = models.ImageField(storage=storage.UserPhotoStorage(), null=True, upload_to=settings.USER_PHOTO_PATH)
    #: The Users preferred Venues
    preferred_venues = models.ManyToManyField('Venue', null=True, related_name='users_who_prefer_this_venue')
    #: if set to true, no emails will be sent by the system to this user
    suppress_emails = PRBooleanField(default=False)
    #: this corresponds to the Django user 'is_staff' field in name only.  Its meaning is
    #: determined by PowerReg variants.  For example, in Constant Contact, it means that the
    #: user does not need to pay anything.
    is_staff = PRBooleanField(default=False)
    #: confirmation code used when we require email confirmation to change a
    #: user's status from 'pending' to 'active' before the user can login. If a
    #: user's status is 'pending' and the confirmation_code is not null, the
    #: user should not be able to login, otherwise continue as usual.
    confirmation_code = models.CharField(max_length=40, null=True)
    #: organization name provided by a user when self-registering.
    alleged_organization = models.CharField(max_length=100, null=True)

    def __str__(self):
        return ('%s %s %s %s' % (self.title, self.first_name, self.last_name,
                                 self.name_suffix)).strip()

    def __unicode__(self):
        return u'%s' % str(self)

    def change_status(self, new_status):
        self.status = new_status

    def _get_username(self):
        try:
            da = self.domain_affiliations.get(default=True)
            return '%s:%s' % (da.domain.name, da.username)
        except DomainAffiliation.DoesNotExist:
            pass
        except DomainAffiliation.MultipleObjectsReturned:
            pass
        return '(no default username)'

    #: derived property that will produce a string of the form 'domain:username'
    #: for the default domain association.  useful for logging, but not intended
    #: for general use (see the default_username_and_domain property of use the
    #: full DomainAssociation model instead for most uses)
    username = property(_get_username)

    def _get_default_username_and_domain(self):
        try:
            da = self.domain_affiliations.get(default=True)
            return {'username': da.username, 'domain': da.domain.name}
        except DomainAffiliation.DoesNotExist:
            return None
        except DomainAffiliation.MultipleObjectsReturned:
            raise exceptions.InternalErrorException('more than one default domain for user with pk %d' %
                self.pk)

    #: derived property that returns a dictionary with 'username' and 'domain'
    #: keys based on the default domain affiliation if one exists.  Returns
    #: None if no default domain association exists.
    default_username_and_domain = property(_get_default_username_and_domain)

    def assign_org_roles_from_email(self):
        # Assign user to organizations and roles based on the domain portion of
        # their email addresses.
        for email in filter(None, (self.email, self.email2)):
            email_domain = email.split('@', 1)[1]
            for org_email_domain in facade.models.OrgEmailDomain.objects.filter(email_domain=email_domain):
                organization = org_email_domain.organization
                org_role = org_email_domain.effective_role
                facade.models.UserOrgRole.objects.get_or_create(owner=self, organization=organization, role=org_role)

    def save(self, *args, **kwargs):
        # When creating a new user, automatically create a confirmation code if
        # needed (based on status and settings).
        new_user = bool(self.pk is None)
        if new_user and getattr(settings, 'USER_EMAIL_CONFIRMATION', False):
            if self.status == 'pending' and self.confirmation_code is None:
                # Based on django-registration's approach for creating a key.
                salt = sha_constructor(str(random.random())).hexdigest()[:5]
                email = self.email
                if isinstance(email, unicode):
                    email = email.encode('utf-8')
                confirmation_code = sha_constructor(salt + email).hexdigest()
                self.confirmation_code = confirmation_code
        super(User, self).save(*args, **kwargs)

    def delete(self):
        for da in self.domain_affiliations.all():
            da.delete()
        super(User, self).delete()

    @property
    def completed_curriculum_enrollments(self):
        return self._get_curriculum_enrollments_by_completion_status(True)

    @property
    def incomplete_curriculum_enrollments(self):
        return self._get_curriculum_enrollments_by_completion_status(False)

    def _get_curriculum_enrollments_by_completion_status(self, status):
        ret = []
        for enrollment in self.curriculum_enrollments.all():
            if enrollment.get_user_completion_status(self) == status:
                ret.append(enrollment)
        return ret


class Blame(OwnedPRModel):
    """
    This object can be attached to any other object for which we want to track
    creation info
    
    relationships:
     - user (1 User to 1 Blame)
     - session (1 Session to 1 Blame)
     - purchase_order (1 PurchaseOrder to 1 Blame)
    """

    #: the User who made the transaction
    user = PRForeignKey(User, related_name = 'blamed_user')
    ip = models.IPAddressField()
    time = models.DateTimeField(auto_now = True)

    def __str__(self):
        return "(%s,%s,%s)" % (str(self.user), str(self.ip), str(self.time))
    def __unicode__(self):
        return u'%s' % (str(self))

#: This is for use by Session and SessionTemplate, which is why it's in this namespace. Remember to update
#: the docs in the manager_svc files any time you change this.
MODALITY_CHOICES = (('ILT', 'ILT'),
                    ('ILT with Remote Labs', 'ILT with Remote Labs'),
                    ('Self-Paced with Remote Labs', 'Self-Paced with Remote Labs'),
                    ('Self-Paced E-Learning', 'Self-Paced E-Learning'),
                    ('Generic', 'Generic'),
                    )


class SessionTemplate(OwnedPRModel):
    """
    a template for a Session.
    """

    sequence = models.PositiveIntegerField(null=True)
    shortname = models.CharField(max_length=31, unique=True)
    fullname = models.CharField(max_length=255)
    version = models.CharField(max_length=15)
    description = models.TextField()
    #: Description of the intended audience
    audience = models.CharField(max_length=255, null = True)
    #: price measured in training units
    price = models.PositiveIntegerField()
    #: lead time for the SessionTemplate in seconds
    lead_time = models.PositiveIntegerField()
    duration = models.PositiveIntegerField(null = True)
    product_line = PRForeignKey(ProductLine, null=True)
    notes = models.ManyToManyField(Note, related_name = 'session_templates')
    active = PRBooleanField(default = True)
    modality = models.CharField(max_length = 31, choices = MODALITY_CHOICES, default='Generic')
    event_template = PRForeignKey('EventTemplate', related_name='session_templates', null=True)

    def __str__(self):
        return '(%s, %s)' % (self.shortname, self.fullname)    
    def __unicode__(self):
        return u'%s' % (str(self))


class Venue(OwnedPRModel):
    """
    A Venue is a location at which an Session occurs
    
    relationships:
      - address (1 Venue to 0..1 Address)
      - session (1 Session to 0..1 Venue)
      - region (1 Venue to 0..1 Region)
    """

    active = PRBooleanField(default=True)
    address = PRForeignKey(Address, null=True, related_name='venues')
    blame = PRForeignKey(Blame, null=True)
    contact = models.CharField(max_length=63, null=True)
    #: store a human readable string containing the hours of operation for the Venue
    hours_of_operation = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    notes = models.ManyToManyField(Note, related_name='%(class)s')
    phone = models.CharField(max_length=31)
    region = PRForeignKey(Region, related_name='venues')

    def __str__(self):
        return self.name
    def __unicode__(self):
        return u'%s' % (self.name)


class Room(OwnedPRModel):
    blame = PRForeignKey(Blame, null=True)
    venue = PRForeignKey(Venue, related_name='rooms')
    room_number = models.CharField(max_length=15)
    name = models.CharField(max_length=63)
    capacity = models.PositiveIntegerField()
    notes = models.ManyToManyField(Note, related_name='rooms')

    def get_remaining_capacity(self, start, end):
        """
        For a given block of time, does this Room have extra capacity?

        @param start    Start of the block of time in question
        @type  start    datetime
        @param end      End of the block of time in question
        @type  end      datetime

        @return         remaining capacity in people
        @rtype          int
        """
        
        surrs = SessionUserRoleRequirement.sort_by_time_block(start, end, self.get_surrs_by_time(start, end))

        for surr_set in surrs:
            assigned = 0
            for surr in surr_set:
                assigned += surr.confirmed_assignments
                if assigned >= self.capacity:
                    break
        return max(0, self.capacity - assigned)

    def get_surrs_by_time(self, start, end):
        """
        For a given block of time, return a QuerySet of all SessionUserRoleRequirements
        that occur partially or completely during that time in this Room.

        @param start    Start of the block of time in question
        @type  start    datetime
        @param end      End of the block of time in question
        @type  end      datetime
        
        @return         QuerySet of SessionUserRoleRequirements
        @rtype          QuerySet
        """

        return SessionUserRoleRequirement.objects.filter(session__room__id=self.id, session__start__lt = end) and \
            SessionUserRoleRequirement.objects.filter(session__room__id = self.id, session__end__gt = start)

    def validate(self, validation_errors=None):
        if validation_errors is None:
            validation_errors = dict()
        
        validation_errors = PRModel.validate(self, validation_errors)
        
        # make sure that Room names are unique within Venues
        possible_duplicates = self.venue.rooms.filter(name=self.name)
        # exclude ourself if we're updating
        if self.pk:
            possible_duplicates = possible_duplicates.exclude(pk=self.pk)
        if not queryset_empty(possible_duplicates):
            add_validation_error(validation_errors, 'name',
                u"Name conflicts with another Room in the same Venue.")
        
        return validation_errors


class Session(OwnedPRModel):
    """
     - template (1 Session to 0..1 SessionTemplate)
     - venue (1 Session to 0..1 Venue)
     - region (1 Session to 0..1 Region)
     - blame (1 Session to 1 Blame)
     - session_user_role_requirement (1 Session to 0..1 SessionUserRoleRequirement)
     - session_template_user_role_requirement (1 SessionTemplateUserRoleRequirement to
                                     1 SessionUserRole)
     - session_resource_type_requirement (1 Session to
                                        0..* SessionResourceTypeRequirements)
       [session_resource_type_requirements]
    """

    #: default price measured in training units
    default_price = models.PositiveIntegerField()
    room = PRForeignKey(Room, null=True, related_name='sessions')
    evaluation = PROneToOneField('Exam', null=True, related_name='session')
    start = models.DateTimeField()
    end = models.DateTimeField()
    session_template = PRForeignKey(SessionTemplate, null=True, related_name='sessions')
    name = models.CharField(max_length=255, unique=True)
    #: description of the intended audience
    audience = models.CharField(max_length=255, null=True)
    title = models.CharField(max_length=127, null=True)
    graphic = models.ImageField(null=True, upload_to='graphics/')
    #: lead time for the Session in seconds
    notes = models.ManyToManyField(Note, related_name='sessions')
    confirmed = PRBooleanField(default=False)
    STATUS_CHOICES = (
        ('active', 'active'),
        ('pending', 'pending'),
        ('proposed', 'proposed'),
        ('canceled', 'canceled'),
        ('completed', 'completed')
    )
    status = models.CharField(max_length = 63, choices = STATUS_CHOICES)
    url = models.URLField(max_length = 255, null = True, verify_exists=False)
    blame = PRForeignKey(Blame, null=True)
    active = PRBooleanField(default=True)
    modality = models.CharField(max_length=31, choices=MODALITY_CHOICES, default='Generic')
    description = models.TextField(null = True)
    event = PRForeignKey('Event', related_name = 'sessions')
    sent_reminders = PRBooleanField(default=False)

    def __unicode__(self):
        if self.session_template:
            return u'name: %s, template: %s, event name: %s' % (self.name, unicode(self.session_template),
                                                                self.event.name)
        else:
            return u'name: %s, event name: %s' % (self.name, self.event.name)

    @staticmethod
    def mangle_id(id):
        return '%04X' % (id + 37)

    @staticmethod
    def unmangle_id(id):
        try:
            return int(str(id), 16) - 37
        except (ValueError, TypeError):
            raise exceptions.InvalidSessionEvaluationCodeException()

    def validate(self, validation_errors=None):
        if validation_errors is None:
            validation_errors = dict()
        
        validation_errors = super(Session, self).validate(validation_errors)

        if not self.start <= self.end:
            add_validation_error(validation_errors, 'start',
                u'Session start time must come before Session end time')
        
        if not self.start >= datetime(self.event.start.year,
            self.event.start.month, self.event.start.day):
            
            add_validation_error(validation_errors, 'start',
                u"starting time %s is not on or after event's starting time %s" %\
                (unicode(self.start), unicode(self.event.start)))
        if not self.end < (datetime(self.event.end.year,
            self.event.end.month, self.event.end.day) + timedelta(days=1)):
            
            add_validation_error(validation_errors, 'end',
                u"ending time %s is not before or on event's ending time %s" %\
                (unicode(self.end), unicode(self.event.end)))
        
        return validation_errors


class EventTemplate(OwnedPRModel):
    """
    This is a collection of values that can be used to pre-populate an Event object.
    For now, the UI client is responsible for fetching these values and applying them
    to a new Event.
    """

    description = models.TextField()
    #: Use this field to store a reference to an entity in a different,
    #: customer-specific data source that corresponds to this Event.
    external_reference = models.CharField(max_length=255, blank=True, null=True)
    facebook_template = models.CharField(max_length=255, default='I just signed up for {{event}}! Click the link to join me.')
    #: Amount of time after an event in seconds at which the event should be marked completed, and e-mails should be sent out
    lag_time = models.PositiveIntegerField(null=True)
    #: Amount of time before an e-mail reminder should be sent, in seconds, relative to the start time of the event
    lead_time = models.PositiveIntegerField(null=True)
    name_prefix = models.CharField(max_length=255)
    notes = models.ManyToManyField(Note, related_name='event_templates')
    organization = PRForeignKey('Organization', related_name='event_templates', null=True)
    product_line = PRForeignKey(ProductLine, related_name='event_templates', null=True)
    title = models.CharField(max_length=127, null=True)
    twitter_template = models.CharField(max_length=255, default='I just signed up for {{event}}! Join me! {{url}}')
    #: A url for the Event
    url = models.URLField(max_length=255, null=True, verify_exists=False)
    
    def __unicode__(self):
        return unicode(self.title)


class Event(OwnedPRModel):
    """
    An Event represents a collection of zero or more Sessions.  The Event has dates, where the Session has times.  The Event also has a Venue, where Sessions have Rooms.
    """

    name = models.CharField(max_length=255)
    region = PRForeignKey(Region, null=True, related_name = 'events')
    title = models.CharField(max_length=127, null=True)
    description = models.TextField()
    start = models.DateField()
    end = models.DateField()
    notes = models.ManyToManyField(Note, related_name='events')
    venue = PRForeignKey(Venue, related_name='events', null=True)
    product_line = PRForeignKey(ProductLine, related_name='events')
    #: Amount of time before an e-mail reminder should be sent, in seconds, relative to the start time of the event
    lead_time = models.PositiveIntegerField(null=True)
    #: Amount of time after an event in seconds at which the event should be marked completed, and e-mails should be sent out
    lag_time = models.PositiveIntegerField(null=True)
    #: Use this field to store a reference to an entity in a different,
    #: customer-specific data source that corresponds to this Event.
    external_reference = models.CharField(max_length=255, blank=True, null=True)
    #: A url for the Event
    url = models.URLField(max_length=255, null=True, verify_exists=False)
    facebook_template = models.CharField(max_length=255, default='I just signed up for {{event}}! Click the link to join me.')
    twitter_template = models.CharField(max_length=255, default='I just signed up for {{event}}! Join me! {{url}}')
    organization = PRForeignKey('Organization', related_name='events')
    event_template = PRForeignKey('EventTemplate', related_name='events', null=True)

    def _get_facebook_message(self):
        t = Template(self.facebook_template)
        if self.url is None:
            url = ''
        else: url = self.url
        context = {'event' : self.title, 'url': url}
        c = Context(context)
        return t.render(c)

    facebook_message = property(_get_facebook_message)

    def _get_twitter_message(self):
        t = Template(self.twitter_template)
        if self.url is None:
            url = ''
        else: url = self.url
        context = {'event' : self.title, 'url': url}
        c = Context(context)
        return t.render(c)

    twitter_message = property(_get_twitter_message)

    def __unicode__(self):
        return unicode(self.title)
    
    def get_status(self):
        """
        Returns the status for an Event based on the statuses of its Sessions. The algorithm is detailed below.

        @returns the Event's status (derived from its Sessions' statuses)
        @rtype string

        <pre>
        Proposed:   All Sessions of this Event have a proposed status. 
        Pending:    At least one Session has a pending status.
        Active:     At least one Session of this Event has an active status. All Sessions of this Event are either active, completed
                    or canceled.
        Completed:  At least one Session of this Event has completed status. All other Sessions are either completed or canceled.
        Canceled:   All Sessions of this Event have canceled status. 
        </pre>
        """
        sessions = self.sessions.all()
        status = None
        if sessions.count() == sessions.filter(status='proposed').count():
            status = 'proposed'
        elif sessions.filter(status='pending').count():
            status = 'pending'
        elif sessions.filter(status='active').count() + sessions.filter(status='completed').count() + \
                sessions.filter(status='canceled').count() == sessions.count():
            status = 'active'
        elif sessions.filter(status='completed').count() + sessions.filter(status='canceled').count() == sessions.count():
            status = 'completed'
        elif sessions.count() == sessions.filter(status='canceled').count():
            status = 'canceled'
        else:
            raise exceptions.EventStatusUnknownException()
        return status

    def validate(self, validation_errors=None):
        if validation_errors is None:
            validation_errors = dict()
        
        validation_errors = PRModel.validate(self, validation_errors)
        
        try:
            old_event = Event.objects.get(id = self.id)
        except Event.DoesNotExist:
            old_event = None
        right_now = date.today()
        one_day = timedelta(days=1)
        if isinstance(self.start, datetime):
            self.start = self.start.date()
        if isinstance(self.end, datetime):
            self.end = self.end.date()
        if old_event is not None and isinstance(old_event.start, datetime):
            old_event.start = old_event.start.date()

        if not self.start <= self.end:
            add_validation_error(validation_errors, 'start',
                u'Event start time must come before Event end time')

        if (self.start < right_now-one_day) and ((old_event is None) or (old_event.start != self.start)):
            add_validation_error(validation_errors, 'start', u'Event start time must not be in the past')

        return validation_errors


class SessionUserRole(OwnedPRModel):
    """
    roles that Users can have at Sessions
    
    relationships:
     - session_user_role_requirement (0..* SessionUserRoleRequirement to 1 SessionUserRole)
       [session_user_role_requirements]
     - session_template_user_role_requirement (1 SessionTemplateUserRoleRequirement to 1 SessionUserRole)
    """

    name = models.CharField(max_length=255, unique=True)
    notes = models.ManyToManyField(Note, related_name = 'session_user_roles')
    active = PRBooleanField(default = True)

    def __str__(self):
        return self.name
    def __unicode__(self):
        return u'%s' % (str(self))


class ResourceType(OwnedPRModel):
    """
    This has a many-to-many relationship with the Resource class.
    
    relationships:
     - session_tempalte_resource_type_requirement (1 SessionTemplateResourceTypeRequirement
                                         to 1 ResourceType)
     - session_resource_type_requirement (1 SessionResourceTypeRequirement
                                        to 1 ResourceType)
    """

    name = models.CharField(max_length=255, unique=True)
    resources = models.ManyToManyField(Resource, related_name='resource_types')
    notes = models.ManyToManyField(Note, related_name = 'resource_types')
    active = PRBooleanField(default = True)

    def __str__(self):
        return self.name
    def __unicode__(self):
        return u'%s' % (str(self))


class SessionUserRoleRequirement(Task):
    """
    Defines a role for a Session, how many Users may fill the role, what
    CredentialTypes they must have,  and which Users are filling the role
    
    relationships:
     - session (1 Session to 0..1 SessionUserRoleRequirement)
     - session_user_role (1 SessionUserRoleRequirement to 1 SessionUserRole)
    """

    session_user_role = PRForeignKey(SessionUserRole,
            related_name='session_user_role_requirements')
    credential_types = models.ManyToManyField(CredentialType,
            related_name='session_user_role_requirements')
    notes = models.ManyToManyField(Note, related_name='session_user_role_requirements')
    active = PRBooleanField(default=True)
    session = PRForeignKey(Session, related_name='session_user_role_requirements')
    enrollment_status_test = PRForeignKey('ConditionTestCollection', related_name='session_user_role_requirements', null=True)
    ignore_room_capacity = PRBooleanField(default=False)

    @property
    def remaining_capacity(self):
        remaining_assignments = super(SessionUserRoleRequirement, self).remaining_capacity
        if self.remaining_room_capacity is None:
            return remaining_assignments
        else:
            return min(remaining_assignments, self.remaining_room_capacity)

    @property
    def remaining_room_capacity(self):
        have_room = hasattr(self.session, 'room') and self.session.room
        if have_room and not self.ignore_room_capacity:
            return self.session.room.get_remaining_capacity(self.session.start, self.session.end)
        else:
            return None

    @staticmethod
    def sort_by_time_block(start, end, surrs):
        """
        For a given block of time and iterable of SessionUserRoleRequirements,
        sort the surrs into blocks of time where one set of surrs extends from
        start to end.

        Example usage is when you need to find the highest enrollment number in
        a Room during a block of time with overlapping SURRs.  You would find
        those SURRs, run them through this method, and then find the total
        enrollment for each resulting set. 

        @param  start    Start of the block of time in question
        @type  start    datetime
        @param end      End of the block of time in question
        @type  end      datetime
        
        @return         list of sets of SessionUserRoleRequirements
        @rtype          set
        """

        # We define sets by identifying the endpoints of SURRs.
        endpoints = [start, end]

        for surr in surrs:
            if surr.session.start > start and surr.session.start < end and surr.session.start not in endpoints:
                endpoints.append(surr.session.start)
            if surr.session.end < end and surr.session.end > start and surr.session.end not in endpoints:
                endpoints.append(surr.session.end)

        endpoints.sort()

        ret = []

        for count in range(len(endpoints) - 1):
            members = set([])
            segment_start = endpoints[count]
            segment_end = endpoints[count + 1]
            for surr in surrs:
                if segment_start >= surr.session.start and segment_end <= surr.session.end:
                    members.add(surr)
            ret.append(members)
        return ret

    def __str__(self):
        return '(%s,%d,%d)' % (str(self.session_user_role), self.min, self.max)
    def __unicode__(self):
        return u'%s' % (str(self))


class SessionTemplateUserRoleReq(OwnedPRModel):
    """
    Template for SessionUserRoleRequirement
    
    relationships:
     - session_user_role (1 SessionTempalteUserRoleRequirement to 1 SessionUserRole)
     - session_template (1 SessionTemplateUserRoleRequirement to 1 SessionTemplate)
    """

    session_user_role = PRForeignKey(SessionUserRole)
    min = models.PositiveIntegerField()
    max = models.PositiveIntegerField()
    session_template = PRForeignKey(SessionTemplate, related_name = 'session_template_user_role_requirements')
    notes = models.ManyToManyField(Note, related_name = 'session_template_user_role_requirements')
    active = PRBooleanField(default = True)

    def __str__(self):
        return '(%s,%d,%d)' % (str(self.session_user_role), self.min, self.max)
    def __unicode__(self):
        return u'%s' % (str(self))


class AuthToken(OwnedPRModel):
    """
    represents a token which uniquely identifies an authenticated session
    """

    session_id = models.CharField(max_length=32, unique=True, db_index=True)
    domain_affiliation = PRForeignKey('DomainAffiliation', related_name='auth_tokens')
    issue_timestamp = models.DateTimeField()
    renewal_timestamp = models.DateTimeField(null=True)
    number_of_renewals = models.PositiveIntegerField()
    #: The tokens may be renewed any number of times.
    time_of_expiration = models.DateTimeField()

    #: The ip address gets corrected by the rpc.amf.PRGateway class
    ip = models.IPAddressField(default = '0.0.0.0')
    active = PRBooleanField(default = True)

    def __str__(self):
        return self.session_id

    def __unicode__(self):
        return u'%s' % (self.session_id)

    def _get_user(self):
        return self.domain_affiliation.user

    user = property(_get_user)


class SingleUseAuthToken(AuthToken):
    """
    like an ordinary AuthToken, but it can only be used once and it has a
    longer expiration time; intended for use with operations that can take
    longer than the expiration time of an AuthToken (such as uploads)
    """
    used = PRBooleanField(default = False)


class AuthTokenVoucher(OwnedPRModel):
    """
    knowledge of this session_id entitles a user to obtain an auth_token one time
    """

    session_id = models.CharField(max_length=32, unique=True)
    domain_affiliation = PRForeignKey('DomainAffiliation', related_name='auth_token_vouchers')
    issue_timestamp = models.DateTimeField()
    time_of_expiration = models.DateTimeField()

    def __str__(self):
        return self.session_id

    def __unicode__(self):
        return u'%s' % (self.session_id)


class SessionTemplateResourceTypeReq(OwnedPRModel):
    """
    Defines a resource type that is required by a SessionTemplate 
    
    relationships:
     - resource_type (1 SessionTemplateResourceTypeRequirement to 1 ResourceType)
     - session_template (1 SessionTemplate to 0..* SessionTemplateResourceTypeRequirement)
    """

    resource_type = PRForeignKey(ResourceType, related_name='%(class)ss')
    session_template = PRForeignKey(SessionTemplate, related_name='session_template_resource_type_requirements')
    min = models.PositiveIntegerField()
    max = models.PositiveIntegerField()
    notes = models.ManyToManyField(Note, related_name = 'session_template_resource_type_requirements')
    active = PRBooleanField(default = True)


class SessionResourceTypeRequirement(OwnedPRModel):
    """
    Defines a resource type that is required by a Session.
    
    This also includes Resources used to fulfill the requirement.
    
    relationships:
     - resource_type (1 SessionResourceTypeRequirement to 1 ResourceType)
     - session (1 Session to 0..* SessionResourceTypeRequirements)
       [session_resource_type_requirements]
    """

    resource_type = PRForeignKey(ResourceType, related_name='%(class)ss')
    #: actual Resources that fill this requirement
    resources = models.ManyToManyField(Resource, related_name='session_resource_type_requirements')
    session = PRForeignKey(Session)
    min = models.PositiveIntegerField()
    max = models.PositiveIntegerField()
    notes = models.ManyToManyField(Note, related_name = 'session_resource_type_requirements')
    active = PRBooleanField(default = True)


class PurchaseOrder(OwnedPRModel):
    """
    Purchase order, generated before the purchase is completed.  This could
    potentially sit around for a while before the customer decides to pay.
    
    relationships:
     - Organization (1 PurchaseOrder to 0..1 Organization)
     - user (1 PurchaseOrder to 0..1 User)
     - blame (1 PurchaseOrder to 1 Blame)

    ** A purchase order must be associated with a Organization or a User, but
       not both. **
    """

    # Exactly one of organization and User should be defined.
    #: Organization this purchase order is for
    organization = PRForeignKey(Organization, null = True, related_name='purchase_orders')
    #: user this purchase order is for
    user = PRForeignKey(User, null = True)
    blame = PRForeignKey(Blame, null=True)
    training_units_purchased = models.PositiveIntegerField(default=0)
    #: total price for the training units, measured in cents
    training_units_price = models.PositiveIntegerField(default=0)
    #: Products sold directly
    products = models.ManyToManyField('Product', related_name = 'purchase_orders',
            through = 'ProductClaim')
    #: Products sold through a user's store front
    product_offers = models.ManyToManyField('ProductOffer', related_name = 'purchase_orders',
            through = 'ClaimProductOffers')
    product_discounts = models.ManyToManyField('ProductDiscount', related_name = 'purchase_orders')
    #: time before which a payment must be made
    expiration = models.DateTimeField(null = True)
    notes = models.ManyToManyField(Note, related_name = 'purchase_orders')
    active = PRBooleanField(default = True)
    #: Promo code entered by the owner, which may or may not be valid
    promo_code = models.CharField(max_length=15, null=True)

    def _get_product_discounts(self):
        """
        get a list of product_discount objects that are valid for use here.
        """

        ret = []
        for claim in self.product_claim.all():
            ret.extend(claim.products.objects.values_list('id', flat=True))
        return ret

    discounts = property(_get_product_discounts)

    def get_template_context(self):
        ret = {}
        ret['first_name'] = self.user.first_name
        ret['last_name'] = self.user.last_name
        if self.user.billing_address:
            ret['billing_address'] = self.user.billing_address
        if self.user.shipping_address:
            ret['shipping_address'] = self.user.shipping_address
        ret['total'] = cents_to_dollars_str(self._get_currency_total())
        ret['products'] = []
        for p in self.products.all():
            ret['products'].append({'sku' : p.sku,
                                    'name' : p.name,
                                    'description' : p.description,
                                    'price' : cents_to_dollars_str(p.price),
                                    'quantity' : ProductClaim.objects.get(purchase_order__id = self.id, product__id = p.id).quantity,
                                    })
        ret['payments'] = []
        for p in self.payments.all():
            ret['payments'].append({'amount' : cents_to_dollars_str(p.amount),
                                    'card_last_four' : p.card_number[-4:],
                                    'time' : p.blame.time,
                                    })
        return ret

    def _get_currency_total(self):
        """
        Calculate the total billable value of this purchase order,
        iterating through Products
    
        @return total value in cents
        """

        return sum(self.product_claims.values_list('price_paid', flat=True)) + self.training_units_price

    def _get_training_unit_total(self):
        """
        Calculate the total billable value of this purchase order,
        iterating through Products
    
        @return total value in cents
        """

        return sum(self.product_claims.objects.values_list('training_units_paid', flat=True))

    total_price = property(_get_currency_total)
    total_training_units = property(_get_training_unit_total)

    def _is_paid(self):
        """
        Is this purchase order paid for?
        
        @return boolean
        """

        money = sum(self.payments.values_list('amount', flat = True))
        if money >= self._get_currency_total():
            return True
        else:
            return False

    is_paid = property(_is_paid)


class TrainingUnitAccount(OwnedPRModel):
    """
    Account that tracks how many training units a person or Organization has available for use

    ** Each instance must be associated with a Organization or a User, but not
    both **.
    """

    organization = PRForeignKey(Organization, null = True, related_name='%(class)ss')
    user = PRForeignKey(User, null = True)
    #: If we don't want to keep transaction history for all of time, we can
    #: throw away history and adjust this value
    starting_value = models.PositiveIntegerField(default = 0)
    blame = PRForeignKey(Blame, null=True)
    active = PRBooleanField(default = True)
    notes = models.ManyToManyField('Note')


class TrainingUnitTransaction(OwnedPRModel):
    """
    Transactions agains a TrainingUnitAccount
    """

    training_unit_account = PRForeignKey(TrainingUnitAccount,
            related_name = 'training_unit_transactions')
    blame = PRForeignKey(Blame, null=True)
    #: monetary value in US cents
    value = models.IntegerField()
    purchase_order = PRForeignKey(PurchaseOrder, related_name = 'training_unit_transactions')
    active = PRBooleanField(default = True)
    notes = models.ManyToManyField('Note')


class TrainingUnitAuthorization(OwnedPRModel):
    """
    An instance of this class authorizes a User to consume up to max_value
    training units from the specified account between two dates.
    """

    training_unit_account = PRForeignKey(TrainingUnitAccount,
            related_name = 'training_unit_authorizations')
    user = PRForeignKey(User, related_name = 'training_unit_authorizations')
    start = models.DateTimeField()
    end = models.DateTimeField()
    max_value = models.PositiveIntegerField()
    #: Used to track how many training units have already been used.
    transactions = models.ManyToManyField(TrainingUnitTransaction,
            related_name = 'training_unit_authorizations')
    blame = PRForeignKey(Blame, null=True)
    notes = models.ManyToManyField('Note')

    def get_used_value(self):
        return -sum(self.transactions.values_list('value', flat = True))


class TrainingVoucher(OwnedPRModel):
    """
    Entitles a User to enroll in an SessionUserRoleRequirement without paying
    """

    session_user_role_requirement = PRForeignKey(SessionUserRoleRequirement,
            related_name = 'training_vouchers')
    purchase_order = PRForeignKey(PurchaseOrder, null = True, related_name = 'training_vouchers')
    code = models.CharField(max_length = 10)
    blame = PRForeignKey(Blame, null=True)
    notes = models.ManyToManyField(Note, related_name = 'training_vouchers')
    active = PRBooleanField(default = True)


class Payment(OwnedPRModel):
    """
    One payment.  There may be several for a purchase order.  We will
    add any info here that the merchant services provider
    (currently just Paypal or Virtual Merchant) gives us.
    """

    card_type = models.CharField(max_length = 10)
    card_number = models.CharField(max_length = 16)
    exp_date = models.CharField(max_length = 4)
    blame = PRForeignKey(Blame, null=True)
    #: value measured in U.S. cents
    amount = models.PositiveIntegerField()
    first_name = models.CharField(max_length = 63)
    last_name = models.CharField(max_length = 63)
    address_label = models.CharField(max_length = 127)
    city = models.CharField(max_length = 63)
    state = models.CharField(max_length = 63)
    zip = models.CharField(max_length = 15)
    country = models.CharField(max_length = 2)
    sales_tax = models.PositiveIntegerField()
    #: transaction ID as designated by the merchant services provider
    transaction_id = models.CharField(max_length = 63)
    purchase_order = PRForeignKey(PurchaseOrder, related_name = 'payments')
    notes = models.ManyToManyField(Note, related_name = 'payments')
    invoice_number = models.CharField(max_length = 31)
    result_message = models.CharField(max_length = 31)
    # Do not ever store the CVV2 value, because that would violate
    # the terms of use for several credit card organizations.
    active = PRBooleanField(default = True)


class Refund(OwnedPRModel):
    """ Refund """

    #: value measured in cents
    amount = models.PositiveIntegerField()
    payment = PRForeignKey(Payment, related_name = 'refunds')
    result_message = models.CharField(max_length = 31)
    #: transaction ID as designated by the merchant services provider
    transaction_id = models.CharField(max_length = 63)
    blame = PRForeignKey(Blame, null=True)


class CSVData(OwnedPRModel):
    """
    This is used to store uploaded CSV data until it can be used.
    """

    text = models.TextField()
    user = PRForeignKey(User)


class Product(OwnedPRModel):
    """
    Anything that we sell.  If custom action needs to be taken after a sale,
    make it happen with an CustomAction.
    """

    blame = PRForeignKey(Blame, related_name='products', null=True)
    description = models.TextField()
    display_order = models.PositiveIntegerField(null=True, default=None)
    # Cost to us of purchasing this for resale
    cost = models.PositiveIntegerField(null=True)
    name = models.CharField(max_length=127)
    notes = models.ManyToManyField(Note, related_name='products')
    #: US Cents, suggested price at which this should be sold to the end User
    price = models.PositiveIntegerField(null=True)
    sku = models.CharField(max_length=32, unique=True)
    starting_quantity = models.PositiveIntegerField(default=0)
    training_units = models.PositiveIntegerField(null=True)
    custom_actions = models.ManyToManyField('CustomAction', related_name='products')
    visibility_condition_test_collection = PRForeignKey('ConditionTestCollection', null=True)

    def get_inventory(self):
        """
        @return current inventory for a Product via a method on the Product model
        @rtype  int
        """
        return self.starting_quantity + sum(self.product_transactions.values_list('change', flat=True))

    def get_best_price(self, discounts):
        self._debug('get_best_price() called with %d discounts' % (len(discounts)))
        c_discounts = []
        nonc_discounts = []
        for discount in discounts:
            if discount.cumulative:
                c_discounts.append(discount)
            else:
                nonc_discounts.append(discount)

        cumulative = self._get_best_cumulative_typed_price(c_discounts)
        noncumulative = self._get_best_cumulative_typed_price(nonc_discounts)
        return {'price' : min([cumulative['price'], noncumulative['price']]),
                'training_units' : min([cumulative['training_units'], noncumulative['training_units']])}

    def _get_best_cumulative_typed_price(self, discounts):
        """
        Given a list of discounts, this method will determine the best price.  This method does not guarantee that
        a discount should apply.  Up-stream logic should determine which discounts are valid.

        @param discounts    list of ProductDiscount objects, all of which have the same value
                            for their 'cumulative' attribute.
        @return             dictionary with keys 'price' and 'training_units'
        """
        self._debug('_get_best_cumulative_typed_price()')
        ret = {'price' : self.price, 'training_units' : self.training_units}
        if len(discounts) == 0:
            self._debug('no discounts were passed in')
            return ret

        cumulative = discounts[0].cumulative
        self._debug('cumulative = %s' % (str(cumulative)))
        applicable_percentage_discounts = []
        applicable_amount_discounts = []
        for discount in discounts:
            if discount.cumulative != cumulative:
                raise exceptions.InvalidInputException('all discounts must have the same value for their "cumulative" property')
            if discount.products.filter(id=self.id).count() == 1 or discount.products.count() == 0:
                if isinstance(discount.percentage, int) and discount.percentage > 0:
                    applicable_percentage_discounts.append(discount)
                else:
                    applicable_amount_discounts.append(discount)
        self._debug('%d percentage discounts apply to this product' % (len(applicable_percentage_discounts)))
        self._debug('%d amount discounts apply to this product' % (len(applicable_amount_discounts)))

        percentages = [discount.percentage for discount in applicable_percentage_discounts]
        currency_amounts = [discount.currency for discount in applicable_amount_discounts]
        training_unit_amounts = [discount.training_units for discount in applicable_amount_discounts]
        percentages.sort(reverse=True)
        percentages.append(0)
        currency_amounts.sort(reverse=True)
        currency_amounts.append(0)
        training_unit_amounts.sort(reverse=True)
        training_unit_amounts.append(0)

        # Apply amount discounts first, then percentages
        if cumulative:
            for amount in currency_amounts:
                if ret['price'] is not None:
                    ret['price'] -= amount
            for amount in training_unit_amounts:
                if ret['training_units'] is not None:
                    ret['training_units'] -= amount
            for percentage in percentages:
                for key in ret:
                    if ret[key] is not None:
                        ret[key] *= (Decimal(1) - (Decimal(percentage)/Decimal(100)))
        # Take the best amount and percentage discounts, and return the best one
        else:
            percentage_prices = ret.copy()
            amount_prices = ret.copy()
            if ret['price'] is not None:
                ret['price'] = min([ret['price'] * (Decimal(1) - (Decimal(percentages[0])/Decimal(100))), ret['price'] - currency_amounts[0]])
            if ret['training_units'] is not None:
                ret['training_units'] = min([ret['training_units'] * (Decimal(1) - (Decimal(percentages[0])/Decimal(100))), ret['training_units'] - training_unit_amounts[0]])

        return ret 
            

class TaskFee(Product):
    """
    a particular type of product which entitles a user to attempt assignments
    for the given task
    """

    task = PRForeignKey('Task', related_name='task_fees')


class ProductClaim(OwnedPRModel):
    """ through table """

    product = PRForeignKey(Product, related_name='product_claims')
    purchase_order = PRForeignKey(PurchaseOrder, related_name='product_claims')
    quantity = models.PositiveIntegerField(default=1)
    price_paid = models.PositiveIntegerField(null=True)
    training_units_paid = models.PositiveIntegerField(null=True)
    discounts = models.ManyToManyField('ProductDiscount', related_name='product_claims')
    discounts_searched = PRBooleanField(default=False)
    blame = PRForeignKey(Blame, related_name='product_claims', null=True)

    @property
    def task_fee(self):
        product = self.product.downcast_completely()
        if isinstance(product, TaskFee):
            return product
        else:
            return None

    @property
    def is_paid(self):
        return self.purchase_order.is_paid

    @property
    def remaining_paid_assignments(self):
        return self.quantity - self.assignments.all().count() if self.is_paid else 0

    def delete(self, *args, **kwargs):
        """
        adjust the inventory when a claim is deleted
        """
        if 'blame' in kwargs:
            blame = kwargs['blame']
            del kwargs['blame']
        elif 'auth_token' in kwargs:
            blame = facade.managers.BlameManager().create(kwargs['auth_token'])
            del kwargs['auth_token']
        else:
            blame = None
        ProductTransaction.objects.create(product=self.product, blame=blame, change=self.quantity)
        super(ProductClaim, self).delete(*args, **kwargs)

    def set_prices(self, reload_discounts = False):
        """
        Set prices, and figure out which discounts to use if that hasn't been
        done yet.

        @param reload_discounts optional, defaults to False. If True, forces
                                this to reconsider all discounts. Use this option
                                if you enter a new promo_code
        """
        self._debug('set_prices()')
        if not self.discounts_searched or reload_discounts:
            discounts = self._set_discounts()
        else:
            discounts = self.discounts.objects.all()
        prices = self.product.get_best_price(discounts)
        if prices['price'] is not None:
            self.price_paid = prices['price'] * self.quantity
        if prices['training_units'] is not None:
            self.training_units_paid = prices['training_units'] * self.quantity
        if self.price_paid is not None:
            self.price_paid = int(self.price_paid)
        if self.training_units_paid is not None:
            self.training_units_paid = int(self.training_units_paid)
        self.save()

    def _set_discounts(self):
        """
        Find all discounts that can be applied. The promo_code will be loaded
        from the PurchaseOrder.
        """
        self._debug('setting discounts for product %s' % (self.product.name))
        discounts = list(ProductDiscount.objects.filter(active=True).exclude(products__id__gte=0))
        discounts.extend(self.product.product_discounts.filter(active=True))
        self._debug('found %d discounts' % (len(discounts)))
        ret = []

        for discount in discounts:
            self._debug('considering discount %s' % (discount.name))
            something_matched = False
            if not (discount.promo_code is None or discount.promo_code==''):
                if discount.promo_code == self.purchase_order.promo_code:
                    something_matched = True
                else:
                    self._debug('promo code "%s" does not match' % (discount.promo_code))
                    continue
            if isinstance(discount.condition_test_collection, ConditionTestCollection):
                if discount.condition_test_collection.get_result(self.purchase_order.owner) is True:
                    something_matched = True
                else:
                    self._debug('condition test collection does not match')
                    continue
            if discount.products.all().count()>0:
                if discount.products.filter(id=self.product.id).count():
                    something_matched = True
                else:
                    self._debug('discount is limited to products of which this one is not a member')
                    continue

            if something_matched:
                ret.append(discount)

        self._debug('saving %d valid discounts' % (len(ret)))
        self.discounts.add(*ret)
        self.discounts_searched = True
        self.save()

        return ret


class ClaimProductOffers(OwnedPRModel):
    """ through table """

    product_offer = PRForeignKey('ProductOffer')
    purchase_order = PRForeignKey(PurchaseOrder)
    quantity = models.PositiveIntegerField(default=1)
    price_paid = models.PositiveIntegerField(null=True)
    training_units_paid = models.PositiveIntegerField(null=True)
    discounts = models.ManyToManyField('ProductDiscount', related_name='product_claim')

class ProductTransaction(OwnedPRModel):
    """
    Track inventory transactions
    
    By doing this, we avoid a potential race condition where simultaneous Sessions
    could overwrite one or the other's inventory adjustment.  Thus, we calculate 
    inventory numbers on the fly. Use product.starting_quantity to reduce transactions
    to a fixed number, and remove those corresponding transactions. This might make a
    good periodic task.
    """

    product = PRForeignKey(Product, related_name='product_transactions')
    blame = PRForeignKey(Blame, null=True, related_name='product_transactions')
    #: how many entered or left the inventory
    change = models.IntegerField()

class ProductDiscount(OwnedPRModel):
    """
    discounts that are available for Products or ProductOffers.

    ProductDiscounts may be associated with a Product or a
    ProductOffer, but not both.
    """

    active = PRBooleanField(default=True)
    currency = models.PositiveIntegerField(null=True)
    blame = PRForeignKey(Blame, null=True, related_name='product_discounts')
    condition_test_collection = PRForeignKey('ConditionTestCollection', related_name='product_discounts', null=True)
    cumulative = PRBooleanField(default=False)
    notes = models.ManyToManyField('Note')
    percentage = models.PositiveSmallIntegerField()
    products = models.ManyToManyField('Product', related_name='product_discounts')
    product_offers = models.ManyToManyField('ProductOffer', related_name='product_discounts')
    promo_code = models.CharField(max_length=15, null=True)
    name = models.CharField(max_length=63, null=True)
    training_units = models.PositiveIntegerField(null=True)

class ProductOffer(OwnedPRModel):
    """
    This is how a Product is offered for sale.
    """

    product = PRForeignKey(Product, related_name='product_offers')
    #: in US Cents
    price = models.PositiveIntegerField()
    seller = PRForeignKey(User, related_name='product_offers')
    description = models.TextField()
    blame = PRForeignKey(Blame, null=True, related_name='product_offers')
    notes = models.ManyToManyField('Note')

class ConditionTestCollection(PRModel):
    """
    """

    name = models.CharField(max_length=127)
    blame = PRForeignKey(Blame, null=True, related_name='condition_test_collections')

    def get_result(self, user):
        self._debug('get_result()')
        for test in self.condition_tests.all().order_by('sequence'):
            if test.applies_to_user(user):
                return True
        return False

class ConditionTest(PRModel):
    """
    """

    condition_test_collection = PRForeignKey(ConditionTestCollection, related_name='condition_tests')
    sequence = models.PositiveSmallIntegerField()
    groups = models.ManyToManyField('Group', related_name='condition_tests')
    organizations = models.ManyToManyField('Organization', related_name='condition_tests')
    credentials = models.ManyToManyField('Credential', related_name='condition_tests')
    events = models.ManyToManyField('Event', related_name='condition_tests')
    sessions = models.ManyToManyField('Session', related_name='condition_tests')
    session_user_role_requirements = models.ManyToManyField('SessionUserRoleRequirement', related_name='condition_tests')
    start = models.DateTimeField(null=True)
    end = models.DateTimeField(null=True)
    match_all_defined_parameters = PRBooleanField(default=False)
    blame = PRForeignKey('Blame', related_name='condition_tests')

    def applies_to_user(self, user):
        """
        If one of the attributes is true (i.e. the user has a relationship with
        one of the related objects, or the current time is within a specified
        temportal boundary), return True.
        """
        self._debug('applies_to_user() called with user of id %d' % (user.id))
        at_least_one_test_ran = False
        if (self.groups.all().count()>0):
            at_least_one_test_ran = True
            if Group.objects.filter(users__id=user.id).filter(condition_tests__id=self.id).count()>0:
                self._debug('group membership matches')
                if not self.match_all_defined_parameters:
                    return True
            else:
                return False
        if (self.organizations.all().count()>0):
            at_least_one_test_ran = True
            if Organization.object.filter(users__id=user.id).filter(condition_tests__id=self.id).count()>0:
                if not self.match_all_defined_parameters:
                    return True
            else:
                return False
        if (self.credentials.all().count()>0):
            at_least_one_test_ran = True
            if Credential.object.filter(users__id=user.id).filter(condition_tests__id=self.id).count()>0:
                if not self.match_all_defined_parameters:
                    return True
            else:
                return False
        if (self.events.all().count()>0):
            at_least_one_test_ran = True
            if Event.object.filter(users__id=user.id).filter(condition_tests__id=self.id).count()>0:
                if not self.match_all_defined_parameters:
                    return True
            else:
                return False
        if (self.sessions.all().count()>0):
            at_least_one_test_ran = True
            if Session.object.filter(users__id=user.id).filter(condition_tests__id=self.id).count()>0:
                if not self.match_all_defined_parameters:
                    return True
            else:
                return False
        if (self.session_user_role_requirements.all().count()>0):
            at_least_one_test_ran = True
            if SessionUserRoleRequirement.object.filter(users__id=user.id).filter(condition_tests__id=self.id).count()>0:
                if not self.match_all_defined_parameters:
                    return True
            else:
                return False

        right_now = datetime.utcnow()
        if isinstance(self.start, datetime):
            at_least_one_test_ran = True
            if self.start < right_now:
                if not self.match_all_defined_parameters:
                    return True
            else:
                return False
        if isinstance(self.end, datetime):
            at_least_one_test_ran = True
            if self.end > right_now:
                if not self.match_all_defined_parameters:
                    return True
            else:
                return False

        if not at_least_one_test_ran:
            self._debug('no tests ran because no conditions are defined')

        return (self.match_all_defined_parameters and at_least_one_test_ran)


class Course(OwnedPRModel):
    """ 
    This model represents a SCORM course.
    """

    name = models.CharField(max_length=127, null=False)

    def delete(self):
        """
        This custom deletion method will delete the associates Scos first, then will remove the files from the filesystem and delete the Course itself.
        """

        for sco in self.scos.all():
            sco.delete(called_from_course_delete=True)
        course_path = settings.SECURE_MEDIA_ROOT+'/'+settings.COURSE_PATH+str(self.id)
        # Remove the Course from the DB.  We want to do this before deleting the files from the FS to ensure that there were no exceptions before removing all the files
        super(Course, self).delete()
        # Delete everything reachable from the directory course_path,
        # assuming there are no symbolic links.
        # CAUTION:  This is dangerous!  For example, if course_path == '/', it
        # could delete disk files.
        for root, dirs, files in os.walk(course_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        # Finally, remove the directory the course was in
        os.rmdir(course_path)


class Sco(Task):
    """ 
    This is the Shareable Content Object.
    """

    course = PRForeignKey(Course, related_name='scos')
    COMPLETION_REQUIREMENT_CHOICES = [
        # Mark completed because the User has visited all the Scos associated with this course,
        # measured by the existance of ScoSessions that are associated with the appropriate
        # Scos
        ('visit_sco', 'visit_sco'),
        # Mark completed because the User has visited and completed all the Scos associated
        # with the course, measured by having a ScoSession for each Sco of the course with
        # cmi_core_lesson_status == 'completed'
        ('cmi_core_lesson_status__completed', 'cmi_core_lesson_status__completed'),
    ]
    #: mark how a course should be measured as complete.
    completion_requirement = models.CharField(max_length=64, default='visit_sco',
        choices=COMPLETION_REQUIREMENT_CHOICES, null=False)
    data = models.CharField(max_length=1024, null=False)
    url = models.CharField(max_length=1024, null=False)

    def delete(self, called_from_course_delete=False):
        """
        We don't allow deletion of Scos.  Delete the Course instead!
        """

        if not called_from_course_delete:
            raise exceptions.OperationNotPermittedException('Deletion of Scos isn\'t permitted directly.  Please delete the Course instead.')
        super(Sco, self).delete()


class ScoSession(AssignmentAttempt):
    """ 
    This model represents a session of a User interacting with a SCO.
    """

    #: Store the flash shared_object as is
    shared_object = models.TextField()
    #: The following fields are all items from the shared_object broken out for reporting
    #: purposes
    cmi_core_lesson_location = models.PositiveIntegerField(null=True)
    cmi_core_lesson_status = models.CharField(max_length=32, null=True)
    cmi_core_score_max = models.PositiveIntegerField(null=True)
    cmi_core_score_min = models.PositiveIntegerField(null=True)

    @property
    def sco(self):
        sco = self.assignment.task.downcast_completely()
        if isinstance(sco, Sco):
            return sco
        else:
            raise TypeError('Assigned Task is not a Sco')

    def save(self, *args, **kwargs):
        if self.assignment.status != 'completed':
            # If the User hasn't completed the Assignment already, let's check to see if this
            # commit will meet the goals
            if self.sco.completion_requirement == 'visit_sco':
                self.assignment.mark_completed()
            elif self.sco.completion_requirement == 'cmi_core_lesson_status__completed' and \
                    self.cmi_core_lesson_status == 'completed':
                self.assignment.mark_completed()
        super(ScoSession, self).save(*args, **kwargs)

class CachedCookie(OwnedPRModel):
    """This is used to keep authorization data that will be cached in memcache
    through the cookiecache module in the database as well, in case of cache misses.

    """
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()


class CustomAction(PRModel):
    name = models.CharField(max_length=65)
    description = models.CharField(max_length=255)
    function_name = models.CharField(max_length=127)
    blame = PRForeignKey(Blame, related_name='custom_actions')

# vim:tabstop=4 shiftwidth=4 expandtab
