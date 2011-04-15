.. _users_guide:

======================
User's Guide
======================

Introduction
============

The PowerReg system manages reservations and other logistics for
adult education.  It has a services layer/backend that may
be used by any number of user interfaces.  This document describes
how to use that backend via Remote Procedure Call (RPC).  Several
RPC protocols are supported, including AMF and XML-RPC.  The focus
here will be on how to best use the API exposed to RPC clients.

The core PowerReg backend is typically customized to meet each
customer's unique requirements.  These customizations are
typically confined to additions to the data model (usually
through customizing existing models), custom security policies
and roles, and code to import customer-supplied data.  We
will focus only on the core version of the framework here,
documenting significant variations elsewhere.  For the
purposes of this document, "Power Reg", "the backend", and
"the framework" are synonymous.

Overall Structure
=================

The framework is composed of a set of services, most of which
manipulate data in a relational database.  Generally, for
each data model, there will be an associated service that
can be used to create, search for, update, and delete
objects of that type.  Such services usually have names of
the form foo_manager, where foo is the data model name.
These services are called PowerReg object managers, or just
object managers for short.  Other services exist, such as
the support_contactor service, that are not so closely
associated with any particular data model.

Each object manager has at least four methods - create,
update, delete, and get_filtered, with the exception of a
few that don't have a create method.  These behave more or
less as one would expect them to, given their names.

The create method takes several arguments, generally all of the
attributes required to create an object of a given type, followed
by a dictionary of optional attributes.  On successful creation
of a new persistent object, the primary key of the newly created
object is returned.

The update method takes the primary key of a persistent
object and a dictionary that maps field names to new values,
searching for an object with that identifier and updating
it according to the values given.

The delete method deleters a persistent object given its
primary key.  However, the system does not allow deletion of
any object that would invalidate other persistent objects
that refer to it.

Additionally, the backend supports running some tasks
asynchronously.  These tasks include sending reminder
emails to users enrolled in sessions.  They are configured
on the server hosting the backend as cron jobs.

Remote Procedure Call Interface
===============================

The majority of the backend can be reached via a number
of Remote Procedure Call (RPC) protocols, including AMF,
XML-RPC, and SOAP.  Other protocols may be added
as needed, as long as each new protocol contains supports
the following:

 * a dictionary (associative array) datatype
 * a list data type
 * a NULL/None value
 * an arbitrary-length string datatype
 * a 32-bit signed integer datatype
 * Unicode in the UTF-8 encoding

.. note::
   The standard XML-RPC protocol does not support a NULL
   value.  The backend uses an extension to the XML-RPC
   protocol that adds support for NULL values, as
   documented at http://ontosys.com/xml-rpc/extensions.php
   in the "<nil/> value" section.

Return values
-------------

Return values (provided that no RPC fault was encountered) may
take one of two forms, depending on whether an error was
encountered.  In both forms, a dictionary is returned with
a ``status`` key that may point to one of two values --
``"OK"`` or ``"error"``.  If the request is successful
(as indicated by the status attribute's being ``"OK"``),
then the response will include another attribute called
``value`` that contains the return value of the remote
method invoked.  Otherwise, the reponse will contain
an ``error`` attribute that evalutes to a two-element
list, with an integer error code as its first element and
a string error message as its second element.  These
low-level error codes and messages are generally not
intended to be displayed directly to end users, but rather
handled as if they were exceptions thrown by the backend,
which is actually how they originate.

Authentication
--------------

Every method except for the ``user_manager`` service's ``login``
and ``reset_password`` methods requires an authentication token
(auth token) as its first argument, which is viewed as an opaque
string of characters by RPC clients.

.. note::
   When using the backend directly through Python (without RPC),
   auth tokens must be passed as instances of the auth_token
   model, not as strings.  This can be achieved easily by
   searching for the ``auth_token`` object whose ``session_id``
   equals the string representation of the auth token received
   from the ``user_manager`` service's ``login`` through the
   ``auth_token`` model's object manager.

Example
-------

The following interactive Python session demonstrates the
RPC conventions followed by the Power Reg backend::

    >>> import xmlrpclib
    >>> s = xmlrpclib.Server('http://localhost:9999/xmlrpc/', allow_none=True)
    >>> ret = s.user_manager.login('admin', 'admin')
    >>> ret
    {'status': 'OK', 'value': 'bee8d5da3882742b15aaac3a42cd291f'}
    >>> auth_token = ret['value']
    >>> ret = s.user_manager.get_filtered(auth_token, {'exact' : {'username' : 'admin'}}, ['id', 'username', 'status', 'preferred_venues'])
    >>> ret
    {'status': 'OK', 'value': [{'username': 'admin', 'status': 'active', 'id': 1, 'preferred_venues': []}]}
    >>> ret = s.user_manager.get_filtered(auth_token, {'exact' : {'username' : 'admin'}}, ['id', 'martians', 'username', 'status', 'preferred_venues'])
    >>> ret
    {'status': 'error', 'error': [4, 'field name not recognized: martians']}
    >>> s.user_manager.logout(auth_token)
    {'status': 'OK', 'value': {}}

Note the URL used to access the backend's XML-RPC interface.  Generally,
the last part of the URL used specifies which RPC protocol to use.  Also
note that Python uses curly braces when displaying dictionaries and
square brackets when displaying lists.
