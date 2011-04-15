.. _datamodel-model_base_classes:

==================
Model Base Classes
==================

The classes documented here are used as base classes for a significant
number of models in the PowerReg system.

.. module:: pr_services.models

.. class:: PRModel

   Abstract base class used for practically all models in the PowerReg
   system.

   superclass: :class:`django.db.models.Model`

.. class:: OwnedPRModel

   Abstract base class that extends :class:`PRModel` by adding a
   foreign-key reference to the :class:`User` model to specify an
   object's owner.

   superclass: :class:`PRModel`

   .. attribute:: owner

      Foreign key reference to the object's owner (ForeignKey field,
      to = :class:`User`, may be null)

.. class:: Versionable

   Abstract base class to facilitate storing version information on
   a model.  Versioning is optional for instances of classes that
   inherit from this one -- a :attr:`version_id` of ``None``
   means not versioned.  Typically a model that inherits from this
   class will have a field called something like ``name`` that must
   be unique when combined with the versioning information stored in these
   fields.

   superclass: :class:`django.db.models.Model`
    
   .. attribute:: version_id

      The numeric version number for this object.  If not null, it should
      be the definitive way to order this object relative to other versions of it.
      Generally, the model using this will have a field such as ``name`` field
      that must be unique together with this field.  If null, the object
      is not versioned.

      (PositiveIntegerField, may be null)

   .. attribute:: version_label

      This attribute may be used to specify a meaningful label for this
      version (for example, a date, a Mercurial changeset id, a CVS
      or Subversion tag name, etc.)  May be left blank.  If not blank,
      should be unique together with :attr:`version_id`.

      (CharField, max length 255, may be blank, default is '')

   .. attribute:: version_comment

      Optional comment to describe this version.  Should be blank
      if :attr:`version_id` is None.

      (CharField, max length 255, may be blank, default is '').

