.. _third_party_authentication:

==========================
Third Party Authentication
==========================

.. seealso:: :ref:`users_guide`

Introduction
============

It has become necessary to establish a method for a user who is
already authenticated on a business partner's system to
become authenticated on a PowerReg system automatically.

In order to support this requirement, we have promoted
user domains to objects in their own right (see the
:class:`Domain <pr_services.models.Domain>` model), so
that we store additional information to identify a trusted
authentication agent for each domain.  Once an authentication
agent has been authenticated, PowerReg will trust it
to authenticate users in its corresponding domain.  The
authentication agent is permitted to make one remote
procedure call (via the XML-RPC protocol) to a method of
the user manager which gives the authentication agent an
authentication voucher for a particular user in the
authentication agent's domain, provided that trust has been
established with the authentication agent successfully.

Trust of an authentication agent is established through
a combination of observing the IP address used in the RPC
call and a password.  Each domain may specify only one
valid IP address for its authentication agent.

Once an auth token voucher identifier is obtained,
a URL can be constructed that instructs the GUI to exchange 
the given auth token voucher for an actual auth token.
This is done by an HTTP GET parameter called ``at_voucher``
which contains the auth token voucher identifier.  For example,
if the URL to the GUI were
``http://kauffman.poweru.net/`` and an auth token voucher
identifier of ``3583b4c14bfa40ab96d6698709cd5c08`` were received, 
the URL with auth token voucher would be
``http://kauffman.poweru.net/?at_voucher=3583b4c14bfa40ab96d6698709cd5c08``.

RPC Interface
=============

The :ref:`user's guide <users_guide>` gives basic information on how RPC requests
are to be sent and what their responses look like.  The
:meth:`obtain_auth_token_voucher <pr_services.user_system.user_manager.UserManager.obtain_auth_token_voucher>`
method can be used to obtain an
auth token voucher identifier, which is expressed as a 
32-character string.  The service defined by the
:class:`UserManager <pr_services.user_system.user_manager.UserManager>`
class
is exposed under the name `user_manager`, so the call to the
:meth:`obtain_auth_token_voucher <pr_services.user_system.user_manager.UserManager.obtain_auth_token_voucher>`
method would be a call to
``user_manager.obtain_auth_token_voucher`` from an XML-RPC client's
point-of-view.

.. autoclass:: pr_services.user_system.user_manager.UserManager
   :members: obtain_auth_token_voucher

