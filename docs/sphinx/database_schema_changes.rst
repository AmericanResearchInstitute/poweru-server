.. _database_schema_changes:

=======================
Database Schema Changes
=======================

Enterprise
==========

* ticket #3073 added User.middle_name attribute
* ticket #2821 add modeling for task bundles

  * added :class:`TaskBundle <pr_services.models.TaskBundle>`
    and :class:`TaskBundleTaskAssociation <pr_services.models.TaskBundleTaskAssociation>`
    models

* ticket #2235 use Django-South for database schema migrations

Yorktown
========

changeset [7006] ticket #2689
--------------------------------------

* Added several new models as part of the new ``forum`` application.

changeset [6780] ticket #2577 (add version concept to core Task model)
----------------------------------------------------------------------

* added a new abstract model called ``Versionable`` and made the ``Task`` model
  a subclass of it.  This also effects models which are children of
  the ``Task`` model, of course, which are currently ``Exam``, ``Sco``, and ``Video``.
  The fields added by inheriting from ``Versionable`` are ``version_id``,
  ``version_label``, and ``version_comment``.

changeset [6733]; ticket #2569
--------------------------------------

* Added ``parent`` field to the ``Organization`` model.
* Added ``children`` field to the ``Organization`` model.
* Added ``ancestors`` field to the ``Organization`` model.
* Added ``descendants`` field to the ``Organization`` model.

changeset [6473]; ticket #2427
--------------------------------------

* Added ``name_suffix`` field to the ``User`` model.

changeset [6255]; ticket #2178
--------------------------------------

* Removed ``ExamSessionReview`` model (in exam_system).
* Removed ``ResponseReview`` model (in exam_system).

changeset [6254]; ticket #2274
--------------------------------------

* Added ``next_question_pool`` field to the ``QuestionPool`` model (in exam_system).

changeset [6215]; tickets #2178, #2274
--------------------------------------

* Added ``name`` field to the ``Answer`` model (in exam_system).

changeset [6207]; ticket #2176
------------------------------

* Added to the ``Organization`` model

  * added ``email`` field.
  * added ``description`` field.
  * added ``photo`` field.
  * added ``primary_contact_last_name`` field.
  * added ``primary_contact_first_name`` field.
  * added ``primary_contact_office_phone`` field.
  * added ``primary_contact_cell_phone`` field.
  * added ``primary_contact_other_phone`` field.
  * added ``primary_contact_email`` field.

changeset [6182]; ticket #2178
------------------------------

* Merge of new exam_system branch back into trunk.
* Modified the ``Exam`` model

  * Removed the ``flag`` field. This field is no longer used.
  * Removed the ``questions`` many-to-many relationship.
  * Removed the ``ratings`` many-to-many relationship.
  * Removed the ``notes`` many-to-many relationship (no longer used).
  * FIXME

* Added the ``QuestionPool`` model.
* Modified the ``Question`` model.

  * Removed the ``flag`` field.
  * Removed the ``answers`` many-to-many relationship.
  * FIXME

* Modified the ``Answer`` model.

  * Removed the ``flag`` field (no longer used).
  * Removed the ``notes`` many-to-many relationship .
  * FIXME

* Removed the ``Rating`` model.  ``Rating`` is now a type of ``Question``.
* Modified the ``ExamSession`` model.

  * Removed the ``notes`` many-to-many relationship (no longer used).
  * FIXME

* Removed the ``QuestionResponse`` model.
* Removed the ``RatingResponse`` model.
* Added the ``Response`` model to handle responses for all question types
  (including ratings).
* Added the ``ExamSessionReview`` model.
* Added the ``ResponseReview`` model.

changeset [6166]; ticket #2276
------------------------------

* Added Domain model
* Added DomainAffiliation model
* User model no longer has an exposed 'username' attribute, but retains a derived attribute on the model called 'username' which should only be used for internal logging purposes.  It returns the username on a user's default DomainAffiliation, but there are no guarantees.
* Added AuthTokenVoucher model, which is not yet used. It entitles a user to obtain an auth_token within a narrow window of time and should be deleted upon use.

changeset [6089]; ticket #2255
------------------------------

* Archived email messages can now be associated directly with users. The relationship is many-to-many so that in the future, we can support multiple recipients per message.

changeset [5734]; ticket #2042
------------------------------

* The ``EventTemplate`` model now exists.

changeset [5723]; ticket #2042
------------------------------

* The ``Event`` model now has a required foreign key reference
  to the ``Organization`` model.

changeset [5722]; ticket #2042
------------------------------

* ``Company`` model renamed to ``Organization``, added department,
  address, phone, and fax fields

changeset [5703]; ticket #1911
------------------------------

* 'msrp' attributes renamed to 'cost'
* SessionFees and EventFees have been removed, EnrollmentFees
  have been added.  SessionUserRoleRequirements now are associated
  with EnrollmentFees rather than SessionFees.

Ranger
======

changeset [5380]; ticket #1631
------------------------------

* made the ``display_order`` field of the ``pr_services.Product`` model default to None

changeset [5255]; ticket #1695
------------------------------

* added two attributes to the ``pr_services.EncodedVideo`` model: ``epilogue_url`` and
  ``prologue_url``

changeset [5216]; tickets #1786
--------------------------------------

* added ``default=''`` to ``region``, ``locality`` and ``postal_code`` fields in
  ``pr_services.Address`` model

changeset [5180]; ticket #1786
------------------------------

* all of the Gilmore models (``gilmore.models.{LineItem,Order,ShipmentMethod}``) now inherit from
  ``pr_services.models.OwnedPRModel`` rather than ``django.db.models.Model``.  This entails the
  addition of a few fields that should be produced automatically on a ``save`` operation, as
  well as our validation code's being used, also on a  ``save`` operation.  Loading data from
  before this change from a fixture should probably work fine.

changeset [5152]; ticket #1643
------------------------------

* added a new boolean field called ``live`` to the ``pr_services.Video`` model
   
changeset [5100]; ticket #1631
------------------------------

* added a ``display_order`` field to the ``pr_services.Product`` model.  It may be
  null.  We may need to set it to default to ``null`` as well before importing
  fixtures works.
 
changeset [5079]; tickets #1622, #1630
--------------------------------------

* added ``is_staff`` and ``supress_emails`` Boolean fields to ``pr_services.User`` model
 
changeset [5032]; ticket #1699
------------------------------

* added a ``photo`` field to the pr_services.Video`` model for storing thumbnail images
  of videos

changeset [5004]; ticket #1671
------------------------------

* added a ``rejected`` Boolean field to the ``pr_services.Task`` model

changeset [4988]; ticket #1680
------------------------------

* removed the ``keywords`` attribute of the ``pr_services.Video`` model.  We are using tags
  from the django-tagging app instead now.

changeset [4985]; ticket #4985
------------------------------

* registered the ``pr_services.Video`` model with the django-tagging app
 
changeset [4959]; ticket #1633
------------------------------

* renamed the ``pr_services.PRModl`` model to ``pr_services.PRModel``
* renamed the ``owner`` attribute of ``pr_services.SessNotifyCfg`` to ``notify_owner``
* added a ``category`` attribute to the ``pr_services.Video`` model
* added a new ``pr_services.OwnedPRModel`` model, which is a subclass of ``pr_services.PRModel``
  that contains an ``owner`` field, which is a foreign key reference to the
  ``pr_services.User`` model.  Both ``pr_services.PRModel`` and
  ``pr_services.OwnedPRModel`` are abstract models, which means that several database
  tables that correspond to models with have the additional field ``owner``, but not all
  of them.  Many models already had an ``owner`` column, and should be able to be
  left alone for this change.  See the following table for models which are now
  subclasses of ``pr_services.OwnedPRModel``:
   
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | Model                            | Had owner field previously?   | Notes                                                      |
  +==================================+===============================+============================================================+
  | ``Announcement``                 | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Note``                         | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Company``                      | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``CredentialType``               | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Credential``                   | no                            | ``user`` field present                                     |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Task``                         | no                            |                                                            |  
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Assignment``                   | no                            | ``user`` field present                                     |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ProductLine``                  | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Region``                       | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Resource``                     | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Group``                        | no                            | ``managers`` field present                                 |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Role``                         | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ACL``                          | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ACCheckMethod``                | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ACMethodCall``                 | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Address``                      | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``User``                         | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Blame``                        | no                            | ``user`` field present                                     |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessionTemplate``              | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Venue``                        | yes                           |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Room``                         | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Session``                      | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Event``                        | yes                           |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessionUserRole``              | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessionEnrollment``            | no                            | ``user`` field present                                     |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ResourceType``                 | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessionUserRoleRequirement``   | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessionFee``                   | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``EventFee``                     | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessionTemplateUserRoleReq``   | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``AuthToken``                    | no                            | ``user`` field present                                     |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  |``SessionTemplateResourceTypeReq``| no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  |``SessionResourceTypeRequirement``| no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``PurchaseOrder``                | no                            | ``user`` field present                                     |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``TrainingUnitAccount``          | no                            | ``user`` and ``company`` fields present                    |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``TrainingUnitTransaction``      | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``TrainingUnitAuthorization``    | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``TrainingVoucher``              | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Payment``                      | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Refund``                       | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``OrganizationUnit``             | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``CSVData``                      | no                            | ``user`` field present                                     |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``QueuedEmailMessage``           | no                            | abstract model                                             |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``FailedEmailMessage``           | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ArchivedEmailMessage``         | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``EmailTemplate``                | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``NotifyCfg``                    | no                            | ``users`` field is users to notify                         |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessNotifyCfg``                | yes                           | ``owner`` field renamed to ``notify_owner``                |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessEnrollNotifyCfg``          | yes                           | ``owner`` field on parent class renamed to ``notify_owner``|
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessionReminderCfg``           | yes                           | ``owner`` field on parent class renamed to ``notify_owner``|
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessStatChgNotifyCfg``         | yes                           | ``owner`` field on parent class renamed to ``notify_owner``|
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``SessEnrollStatChgNotifyCfg``   | yes                           | ``owner`` field on parent class renamed to ``notify_owner``|
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``UsrRelatedNotifyCfg``          | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``UsrStatChgNotifyCfg``          | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``EmailAddress``                 | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Product``                      | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ClaimProducts``                | no                            | through table                                              |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ClaimProductOffers``           | no                            | through table                                              |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ProductTransaction``           | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ProductDiscount``              | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ProductOffer``                 | no                            | ``seller`` field present                                   |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``PaypalECToken``                | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Answer``                       | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Question``                     | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Exam``                         | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ExamSession``                  | no                            | ``user`` attribute present                                 |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Rating``                       | no                            | ``user`` attribute present                                 |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``RatingResponse``               | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``QuestionResponse``             | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Course``                       | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Sco``                          | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``ScoSession``                   | no                            | ``user`` attribute present                                 |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``CachedCookie``                 | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``Video``                        | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``EncodedVideo``                 | no                            |                                                            |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
  | ``VideoSession``                 | no                            | ``user`` field present                                     |
  +----------------------------------+-------------------------------+------------------------------------------------------------+
    
 

changeset [4909]; ticket #1637
------------------------------

* added ``aspect_ratio`` and ``job_guid`` attributes to the ``pr_services.Video`` model

changeset [4843]; ticket #1641
------------------------------

* added the ``keywords`` attribute to the ``pr_services.Video`` model, which was later
  removed in deference to tags from ``django-tagging`` in changeset [4988]

changeset [4839]; ticket #1650
------------------------------

* added the ``create_timestamp`` and ``save_timestamp`` attributes to the abstract ``pr_services.PRModl`` model:

  See the following table for information about models that already had timestamp attributes:
   
  +----------------------------------+------------------------------------+-------+
  | Model                            | Had timestamp field(s) previously? | Notes |
  +==================================+====================================+=======+
  | ``Announcement``                 | yes, ``create_timestamp``          |       |
  +----------------------------------+------------------------------------+-------+
  | ``Note``                         | yes, ``time``                      |       |
  +----------------------------------+------------------------------------+-------+
  | ``QueuedEmailMessage``           | yes, ``create_timestamp``          |       |
  +----------------------------------+------------------------------------+-------+
  | ``EmailTemplate``                | yes, ``create_timestamp``          |       |
  +----------------------------------+------------------------------------+-------+

.. _database_schema_changes-changeset_4826:

changeset [4826]; ticket #1620
------------------------------

* renamed the ``timestamp`` field on the ``pr_services.Announcement`` model to ``create_timestamp``
* the ``description`` attribute of the ``pr_services.CredentialType`` is now a ``TextField``.  It was
  previously declared as a ``CharField``.
* the ``number`` attribute of the ``pr_services.Room`` model has been renamed to ``room_number``.
  Apparantly, there is also a ``name`` attribute, which we use in AT&T/Lexington to refer to store room numbers.
* renamed the ``timestamp`` field on the ``pr_services.QueuedEmailMessage`` model to ``create_timestamp``
* renamed the ``timestamp`` field on the ``pr_services.EmailTemplate`` model to ``create_timestamp``

changeset [4747]; ticket #1583
------------------------------

* added ``public`` and ``published`` Boolean fields to the ``pr_services.Task`` model, which both
  default to ``False``
* added ``author`` and ``length`` character fields to the ``pr_services.Video`` model
* added a new ``pr_services.EncodedVideo`` model

changeset [4711]
----------------

* removed the ``video`` attribute of the ``pr_services.VideoSession`` model.  This model now has
  no attributes of its own.  The same information can be obtained by its ``task`` attribute, as
  videos are tasks and video sessions are assignments.

changeset [4706]; ticket #1583
------------------------------

* added a new ``pr_services.Video`` model, which is a subclass of ``pr_services.Task``
* added a new ``pr_services.VideoSession`` model, which is a subclass of ``pr_services.Assignment``
 
changeset [4685]; tickets #1582, #572
-------------------------------------

* increased the maximum length of the ``password_hash`` attribute of the ``pr_services.User`` model
  from 127 to 128 
* added a ``password_salt`` attribute to the ``pr_services.User`` model

changeset [4474]; ticket #1454
------------------------------

* changed the ``description`` attribute of the ``pr_services.SessionTemplate`` model from
  a ``CharField`` to a ``TextField``

changeset [4269]; ticket #1268
------------------------------

* a new ``pr_services.ACL`` model has been added, with one-to-many relationship between ``pr_services.Role``
  and ``pr_services.ACL``.  Through this change, the following fields have been removed
  from the ``pr_services.Role`` model and added to the new ``pr_services.ACL`` model
  unless otherwise noted:
   
  * ``active`` (which is not on the ``pr_services.ACL`` model either, as it was obselete)
  * ``ac_check_methods`` (This is a many-to-many field with an association class/through table.
    Making this transition via alteration of an existing database may be difficult.)
  * ``arbitrary_perm_list``

* The ``pr_services.ACMethodCall`` association class (through table/model) now associates
  instances of ``pr_services.ACL`` instead of ``pr_services.Role`` with instances of
  ``pr_services.ACCheckMethod``.  (This could be a difficult change to effect via direct
  alteration of an existing database.)  
   
Saratoga
========
   
changeset [4248]; ticket #427
-----------------------------

* added a ``lag_time`` attribute to the ``pr_services.Event`` model

changeset [4238]; ticket #1388
------------------------------

* instances of ``pr_services.Event`` can no longer be created with ``start`` values in the past.
  I have tested that fixture with events with ``start`` attributes in the past load
  properly.  The validation code on the ``pr_services.Event`` model's ``save()`` method
  considers loading from a fixture not a creation, since the data from the fixture contains
  a primary key value.
