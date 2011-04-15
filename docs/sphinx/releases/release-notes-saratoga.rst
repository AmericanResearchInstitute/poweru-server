.. _release-notes-saratoga:

========================
Release Notes - Saratoga
========================

Backwards-Incompatible Changes
==============================

 * The user_preferences model has been removed in favor of including
   user preferences directly in the core and derived user models.
   `trac #874 <https://trac.americanri.com.ofc/power_reg/ticket/874>`_
 * The user model no longer has an active flag.  Instead, the status
   field is used to determine whether a user is inactive.  See
   `trac #955 <https://trac.americanri.com.ofc/power_reg/ticket/955>`_
 * The UserManager no longer has authenticate(), unauthenticate, or re_authenticate() methods.  Instead, they
   have been replaced with login(), logout(), and relogin(), repectively.  See
   `trac #960 <https://trac.americanri.com.ofc/power_reg/ticket/960>`_
