.. _index:

======================
PowerReg documentation
======================

General
=======

* :ref:`Releases <releases>`
* :ref:`Changelog <changelog>`

User Documentation
==================

* :ref:`User's Guide <users_guide>`
* :ref:`Third Party Authentication <third_party_authentication>`
* :ref:`Exceptions <exceptions_list>`

Development Processes
=====================

* :ref:`Commit Policy <commit_policy>`
* :ref:`Testing Procedures <testing_procedure>`

Subsystems
==========

* :ref:`The Authorizer <subsystems-authorizer>`
* :ref:`Task and Credential Management <subsystems-task-and-credential-management>`
* :ref:`Exams <subsystems-exams>`
* :ref:`subsystems-scorm`
* :ref:`subsystems-upload_manager`

Data model
==========

* :ref:`datamodel-model_base_classes`
* :ref:`Database Schema Changes <database_schema_changes>`
* :ref:`datamodel-getters_and_setters`
* :ref:`Users, Addresses, Groups, and Organizational Units <datamodel-users>`
* :ref:`Events and Sessions <datamodel-events_and_sessions>`
* :ref:`Tasks and Assignments <datamodel-tasks_and_assignments>`
* :ref:`Credentials <datamodel-credentials>`
* :ref:`Roles and Access Control Lists (ACLs) <datamodel-acls>`

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Cruft
=====

.. note::
   While the above is a table of contents, it wasn't written as Sphinx toctree.
   as a result, the toctree is included here to supress Sphinx warnings about
   how nothing's included in the toctree. At the time of writing, adding
   :hidden: to the toctree's options causes an exception to be raised and the
   docs build to fail

.. toctree::
   :glob:

   changelog
   releases/*
   datamodel/*
   subsystems/*
   user_docs/*
   *

