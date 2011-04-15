.. _subsystems-task-and-credential-management:

===============================
Task and Credential Management
===============================

.. seealso:: Data Model :ref:`datamodel-tasks_and_assignments`, :ref:`datamodel-credentials`

Task Management
===============

The task management system works in tandem with the credential
management system. Together, these two sub-systems manage the
relationships between tasks, requirements, prerequisites, and
credentials (also referred to as achievements). 

In the loosest sense, a task in PowerU is any activity which
can be assigned and measured. It is similar to a requirement.
A requirement is any condition which can be measured. The
difference between the two is that a task involves some
action on the part of the user. A requirement does not involve
a user action, but instead depends on an attribute match. 

In this version of PowerU, both tasks and requirements are limited
to items which can be assigned as prerequisites to user achievements.
In later versions, the scope of task management will likely be
expanded to include a plethora of work-flow activities which are
not directly related to the satisfaction of prerequisites or achievements. 

Supported PowerU Task Types include: 

* completing a system exam (surveys and evaluations are not scored)
* achieving a passing score on a system exam
* downloading a file (indirectly indicates user has read the document)
* accepting user license agreement / acceptable use policy
* confirming receipt of information (indirectly indicates intention to comply)
* launching a video
* completing SCORM content
* launching SCORM content

Supported PowerU Requirement Types, by contrast, include:

* matching a specific organizational node
* matching an organizational branch
* holding a specific user status value for a specified period of time (≥ n days)
* matching a specific user slot
* holding current user slot for a specified period of time (≥ n days)
* holding a specific credential 
* holding a specific credential for a specified period of time (≥ n days)

.. note::

   The notion of a user slot is new to PowerU.  Since the addition of
   organizational recursion, it is possible to model an organization map.
   The map is a collection of users, grouped in a hierarchical manner. Each
   member of the organization occupies a single “slot” with a specific
   location on the map. Slots have an associated achievements template. When
   comparing this slot template with an individual user's achievements, the
   delta between the user and the slot can be determined and used to
   influence training plans.

The Task Management System must include both back-end and front-end
components. User roles permitted to use the task management system will
be able to create new tasks, edit existing tasks, assign tasks, unassign
tasks, and view assigned tasks.  This activity may be limited to a certain
user population. For example, an Organization Administrator will typically
be allowed to perform task management activities for members of their own
organization, but not for other organizations.  In a multi-tiered organization,
each level in each branch will have one or more administrators who may
perform task management activities for members of their own organization
as well as all child organizations under their own branch.

Credential Management System
============================

The credential management system works in tandem with the task management
system. Together, these two sub-systems manage the relationships between
tasks, requirements, prerequisites, and credentials (also referred to as
achievements).  

Achievements are automatically earned by meeting all assigned prerequisites.
Achievements and associated prerequisites are managed through the Credential
Management System. Prerequisites are composed of tasks and requirements which
are managed through the Task Management System. Additionally, some achievements
may be granted interactively by administrators without any precondition. For
example, an "employee of the month" award may not require anything but an
administrative selection.  

Achievements may be of one of the following types:

Award
    this type is used for recognition of merit, member of the month, etc

Degree
    this type is used for all academic degrees

Certification
    this type is used for non-degree yielding academic achievements

Renewable Certification
    this type is for certifications which must be renewed

Rank
    this type is used to denote relative position on some scale (discrete or continuous)
    (requires that ranks be defined in the system)    

Once an achievement is granted, it can not be removed by the system. Only
interactive administrative intervention can revoke an achievement.

Prerequisites are groups of tasks or requirements. By making an achievement
dependent on one or more prerequisites, the administrator can more easily
make changes which will apply to many achievements at once.  For example,
award A and award B both have multiple prerequisites, however, one prerequisite
they have in common is titled, "time in current position". Suppose the value
is set to 60 days. If the organizational policy changes to allow awards after
only 30 days, then the administrator may edit this single prerequisite which
has been applied to multiple achievements, rather than edit the value for every award.

The Credential Management System must include both back-end and front-end components.
User roles permitted to use the credential management system will be able to
select tasks and requirements from which to create and edit prerequisites.
Administrators will be able to select one or more prerequisites to associate
with a credential. 

Credential flair is a visual representation of an achievement.
Each credential type may include any of the following types of flair:

* small badge image (size tbd) 
* large badge image (size tbd)
* small cert template (size tbd)
* large cert template (size tbd)

RPC Interface
=============

Task Manager and Task Bundle Manager
------------------------------------

.. module:: pr_services.credential_system.task_manager

.. autoclass:: pr_services.credential_system.task_manager.TaskManager
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

.. module:: pr_services.credential_system.task_bundle_manager

.. autoclass:: pr_services.credential_system.task_bundle_manager.TaskBundleManager
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

Assignment Manager
------------------

.. module:: pr_services.credential_system.assignment_manager

.. autoclass:: pr_services.credential_system.assignment_manager.AssignmentManager
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

Children of the Task Manager and their Collaborators
----------------------------------------------------

.. module:: pr_services.credential_system.video_manager

.. autoclass:: pr_services.credential_system.video_manager.VideoManager
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

.. module:: pr_services.credential_system.encoded_video_manager

.. autoclass:: pr_services.credential_system.encoded_video_manager.EncodedVideoManager
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

ExamManager and ScoManager
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`ExamManager <pr_services.exam_system.exam_manager.ExamManager>` class is
a subclass of the :class:`Task Manager <pr_services.credential_system.task_manager.TaskManager>`
class.  It is documented in :ref:`subsystems-exams`.

The :class:`ScoManager <pr_services.scorm_system.sco_manager.ScoManager>`
class is a subclass of the
:class:`Task Manager <pr_services.credential_system.task_manager.TaskManager>`
class.  It is documented in :ref:`subsystems-scorm`.

