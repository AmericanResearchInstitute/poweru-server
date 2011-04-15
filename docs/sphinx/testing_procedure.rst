.. _testing_procedure:

==================
Testing Procedures
==================

Once a Ticket Has Been Opened During Customer Testing
=====================================================

Triage
------

In this phase, a qualified individual assesses a given problem report (in the form of a ticket),
specifically in regards to the following questions:

 * What version of the product was in use when the problem behavior
   was observed?  Are any other possibly relevant environment factors,
   such as operating system, web browser, and Flash plugin version
   included in the problem report?
 * Does the problem report give sufficient detail to reproduce the problem?
 * Does the problem report clearly state what the expected and actual results are?
 * What subsystems are likely to be involved in the observed behavior?
 * Are other systems external to the product being developed also likely to be
   key to reproducing the problem?  If so, can their interactions be simulated
   at ARI? 
 * How severe does the problem appear to be? (Adjust the ticket priority accordingly.)

If at any point during this phase more information is needed, said individual will
contact the originator of the ticket or other relevant people for clarification.

Assign to Developer
-------------------

Once sufficient detail is obtained, if the problem needs debugging, it will be
assigned to a developer who is familiar with the subsystems assumed to be relevant.
The developer is to cooperate with the person who assigned the ticket to him or
her as needed, as well as with other developers.  If needed, the ticket may
be transferred to a developer who has more expertise in the areas of the code
involved.

Once the ticket has settled on a developer, work on reproducing the problem
can begin if it hasn't already.  Relevant log files or other data may be
requested from the appropriate system administrator(s).  Once a sufficient
understanding of the problem is reached, the developer can move on to
working on a solution to the problem.

Fix and Unit Test
-----------------

Once the developer has arrived at a sufficient understanding of the problem
and determines that a code change is necessary, the developer will develop (if possible)
a unit test that demonstrates the problem and proceed to develop a solution to the
problem.

At this point (or perhaps after the commit), the developer is encouraged
to solicit review from other developers.  The results of said code review
should be noted as comments in the ticket.

Commit
------

Once the developer is satisfied that the problem has been solved and passes
the unit test developed for it (as well as manual testing if applicable),
the developer runs the entire suite of unit tests for the product under development.
Once the developer meets the requirements of the :ref:`Commit Policy <commit_policy>`,
he or she may commit the code change.

Manual Test on ARI Systems
--------------------------

Once the relevant code change(s) have been unit tested and commited, the internal
development environment for the product under development can be updated
to incorporate the code change.  Typically, such development environments are
located on wsgi-dev.americanri.com.ofc.  The developer should contact the ARI
system administrator(s) if assistance is needed in this step.

Once the development instance has been updated, the developer can proceed to
verify that the change has indeed been successfully implemented on the
development server.

The ticket can now be marked as waiting on a new build, specifying exactly
which revisions of the backend or GUI (or both) are required to see the
complete implementation.

New Build
---------

Once the build/release manager decides to produce a new build, he or she
may elect to do a quick review of all of the code changes that have occurred
since the previous build.  This is often most easily done in trac by navigating
to the path of the relevant GUI and backend projects, viewing revision history,
and opening each changeset that occurred after the previous build in a new tab,
closing tabs as each changeset is reviewed.

The build manager will also take note of which tickets are marked as waiting
on a new build.  Once the new build is produced, those tickets can be
quickly tested on the ARI test systems, typically hosted on test.poweru.net.

Deploy Fix on Customer Systems and Retest
-----------------------------------------

Once the new build has been produced and its relevant tickets verified, an
update can be scheduled with the client.  Then (if the solution will be
hosted on the client's systems) the relevant system administrator will update
the installation on the client's system and quickly verify that the changes
have taken effect.

Notify Customer of Fix
----------------------

Once the customer's test installation has been updated, the customer can
be notified of which problems have tested positively as having been
addressed in the current build, as well as the build number and any
documentation of test results that the customer may require (to be negotiated
on a per-customer basis).
