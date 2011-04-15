.. _commit_policy:

=============
Commit Policy
=============

The basic commit policy boils down to one simple rule: Do not break
the trunk. Liberal use of both automated and manual testing as well as
branching and merging are encouraged.  The backend services layer has
an extensive suite of unit tests, which make determining whether you have
broken the trunk easier.  The GUI has a few fledgling unit tests, but is
unfortunately largely tested manually at the time of writing.
The liberal usage of tickets is encouraged, as is 
referring to them in commit log messages.

More specifically, for the backend:
 1. When working on PowerReg core, no checkin on the trunk may proceed unless
    all Django app and RPC unit tests pass.
 2. When working on a variant, the unit tests that are specific to the variant
    (generally the Django unit tests for all of the Django apps present in the
    variant but not in core as well as the RPC unit tests in the variant's
    Django project directory) must be run successfully.
 3. All non-trivial commits to the backend shall be linked to a ticket.  The commit
    messages should contain not only a reference to the ticket or tickets involved
    (e.g., "re #1305"), but also a brief description of the changes made.  A trivial
    change amounts to fixing typos in comments, changing formatting to fit PEP-8,
    etc.
 4. When implementing a new feature that will become part of the services exposed
    via RPC, a unit test should be written for the new code before it is checked into
    the trunk.  More frequent checkins to a branch are encouraged, whether the
    branch is made directly in Subversion or indirectly through svk, git-svn, etc.
 5. When updating an externals definition to use a different version of parts of PowerReg
    core in a variant, the unit tests for the variant must be run before checking
    in the associated property change.  This is really just an elaboration of
    rule number 2.
    