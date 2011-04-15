.. _changelog:

=========
Changelog
=========

Version enterprise
==================

* ticket #3136 add MEDIA_URL setting to context for all email templates (as media_url)
* ticket #3128 added SITE_URL setting and site_url context item for all email templates
* ticket #3095 added mechanism for defining and enforcing password policies
* ticket #3073 added User.middle_name field (includes ACL updates)
* ticket #3072 added derived User.full_name field
* ticket #2892 make new derived property on the User model
  (default_username_and_domain) as a replacement for the
  default_username derived property used by many variants
* ticket #2880 no longer using the empty string as a dictionary
  key for validation errors
* now using Django South for database schema migrations

Version yorktown
================

* ticket #2184 use 'Reply-To' field for help requests and user
  feedback email messages
* ticket #2181 (changeset [5772]) move code to load all of the
  installation default email templates based on the
  EMAIL_TEMPLATE_FIXTURE_DIRS setting from the 'setup'
  Django management command to the InitialSetupMachine
  class

Version ranger.1
================

* update externals to use Django 1.1.1 and the latest available
  version of django-tagging stored in our Subversion repository
* ticket #2194 silently truncate CharField values
* ticket #2188 fix incorrect module prefix in pr_services/gettersetter.py
* ticket #2236 allow usernames with spaces in the local domain
* ticket #2259 pull the email template types directly from the
  ``facade.models.EmailTemplate`` model

Version ranger
==============

* ticket #1923 added a new pr_services.utils.SingleProcessInstance class with
  implementations for Windows and UNIX/Linux.  This adds a dependency on the
  Python processing module for versions of Python earlier than 2.6.  This
  includes a new setting, LOCK_FILE_UNIQUE_STRING, which is a unique
  string to include at the end of names of lock files (or named mutexes
  on Windows)
* ticket #1919 the length of time before an auth token expires is now a setting
* ticket #1910 passwords are no longer checked in the user manager's relogin() method
* added Oracle support
* added a facade for subsystems, managers, models, and RPC manager proxy classes.  Variants
  can use a custom facade that specifies different implementations, and the specified
  implementations will be used in core code that uses the facade to retreive implementation
  classes.
* added support for Boolean expressions in get_filtered() queries
* including django-tagging and added support for filters based on including
  one or more of a list of tags (``tag_union``) or all of a list of tags
  (``tag_intersection``) to the PR object manager's get_filtered() method
* the import manager has been significantly re-worked for CSV file importing
* trac #1626: added the ability for admin users to regenerate or resend payment confirmation emails
  ("receipts")

  * added two arbitrary permissions, ``regenerate_payment_confirmations`` and
    ``resend_payment_confirmations``
  * added a ``generate_preview`` method to the email manager which returns the
    rendered subject, body, and html body given a proposed recipient,
    an email template type ("notification scenario"), and a context
  * added two methods to the purchase order manager, ``retreive_receipt`` and
    ``resend_receipt``

Version saratoga.4 -- 12 August 2009
====================================

* we no longer use distinct() in all Django queries issued via the PR
  object manager's get_filtered() method
* the authorizer is now a singleton

Version saratoga.3 -- 17 July 2009
==================================

* added a changelog (#1607)
* Backported the following tickets:

 * #1570 - add a PYTHON_INTERPRETER setting to tests_svc_settings.py
 * #1415 - don't check for existence of URL's for URLFields
 * #1590 - optional_params argument for email template manager's create method (for html_body)
 * #1594 - missing getters for last_editor and html_body in email template manager
 * #1595 - admin ACL incorrect for email templates 
