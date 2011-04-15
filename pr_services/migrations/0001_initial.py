# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Note'
        db.create_table('pr_services_note', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_notes', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['Note'])

        # Adding model 'Organization'
        db.create_table('pr_services_organization', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_organizations', null=True, to=orm['pr_services.User'])),
            ('primary_contact_first_name', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('primary_contact_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('primary_contact_cell_phone', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('department', self.gf('django.db.models.fields.CharField')(max_length=127, null=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('fax', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('parent', self.gf('pr_services.fields.PRForeignKey')(related_name='children', null=True, to=orm['pr_services.Organization'])),
            ('primary_contact_other_phone', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('address', self.gf('pr_services.fields.PRForeignKey')(related_name='organizations', null=True, to=orm['pr_services.Address'])),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('primary_contact_office_phone', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
            ('primary_contact_last_name', self.gf('django.db.models.fields.CharField')(max_length=31)),
        ))
        db.send_create_signal('pr_services', ['Organization'])

        # Adding unique constraint on 'Organization', fields ['name', 'parent']
        db.create_unique('pr_services_organization', ['name', 'parent_id'])

        # Adding M2M table for field notes on 'Organization'
        db.create_table('pr_services_organization_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['pr_services.organization'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_organization_notes', ['organization_id', 'note_id'])

        # Adding model 'OrgRole'
        db.create_table('pr_services_orgrole', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('default', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['OrgRole'])

        # Adding model 'UserOrgRole'
        db.create_table('pr_services_userorgrole', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('parent', self.gf('pr_services.fields.PRForeignKey')(related_name='children', null=True, to=orm['pr_services.UserOrgRole'])),
            ('role', self.gf('pr_services.fields.PRForeignKey')(related_name='user_org_roles', to=orm['pr_services.OrgRole'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_userorgroles', null=True, to=orm['pr_services.User'])),
            ('organization', self.gf('pr_services.fields.PRForeignKey')(related_name='user_org_roles', to=orm['pr_services.Organization'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['UserOrgRole'])

        # Adding unique constraint on 'UserOrgRole', fields ['owner', 'organization', 'role']
        db.create_unique('pr_services_userorgrole', ['owner_id', 'organization_id', 'role_id'])

        # Adding model 'OrgEmailDomain'
        db.create_table('pr_services_orgemaildomain', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('role', self.gf('pr_services.fields.PRForeignKey')(related_name='org_email_domains', null=True, to=orm['pr_services.OrgRole'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('email_domain', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_orgemaildomains', null=True, to=orm['pr_services.User'])),
            ('organization', self.gf('pr_services.fields.PRForeignKey')(related_name='org_email_domains', to=orm['pr_services.Organization'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['OrgEmailDomain'])

        # Adding unique constraint on 'OrgEmailDomain', fields ['email_domain', 'organization', 'role']
        db.create_unique('pr_services_orgemaildomain', ['email_domain', 'organization_id', 'role_id'])

        # Adding model 'CredentialType'
        db.create_table('pr_services_credentialtype', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_credentialtypes', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['CredentialType'])

        # Adding M2M table for field prerequisite_credential_types on 'CredentialType'
        db.create_table('pr_services_credentialtype_prerequisite_credential_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_credentialtype', models.ForeignKey(orm['pr_services.credentialtype'], null=False)),
            ('to_credentialtype', models.ForeignKey(orm['pr_services.credentialtype'], null=False))
        ))
        db.create_unique('pr_services_credentialtype_prerequisite_credential_types', ['from_credentialtype_id', 'to_credentialtype_id'])

        # Adding M2M table for field notes on 'CredentialType'
        db.create_table('pr_services_credentialtype_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credentialtype', models.ForeignKey(orm['pr_services.credentialtype'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_credentialtype_notes', ['credentialtype_id', 'note_id'])

        # Adding M2M table for field required_achievements on 'CredentialType'
        db.create_table('pr_services_credentialtype_required_achievements', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credentialtype', models.ForeignKey(orm['pr_services.credentialtype'], null=False)),
            ('achievement', models.ForeignKey(orm['pr_services.achievement'], null=False))
        ))
        db.create_unique('pr_services_credentialtype_required_achievements', ['credentialtype_id', 'achievement_id'])

        # Adding model 'Credential'
        db.create_table('pr_services_credential', (
            ('status', self.gf('django.db.models.fields.CharField')(default='pending', max_length=8)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('date_expires', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('authority', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('credential_type', self.gf('pr_services.fields.PRForeignKey')(related_name='credentials', to=orm['pr_services.CredentialType'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_credentials', null=True, to=orm['pr_services.User'])),
            ('serial_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('date_started', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('date_granted', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_assigned', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('pr_services.fields.PRForeignKey')(related_name='credentials', to=orm['pr_services.User'])),
        ))
        db.send_create_signal('pr_services', ['Credential'])

        # Adding M2M table for field notes on 'Credential'
        db.create_table('pr_services_credential_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credential', models.ForeignKey(orm['pr_services.credential'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_credential_notes', ['credential_id', 'note_id'])

        # Adding model 'Achievement'
        db.create_table('pr_services_achievement', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_achievements', null=True, to=orm['pr_services.User'])),
            ('organization', self.gf('pr_services.fields.PRForeignKey')(related_name='achievements', null=True, to=orm['pr_services.Organization'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['Achievement'])

        # Adding M2M table for field component_achievements on 'Achievement'
        db.create_table('pr_services_achievement_component_achievements', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_achievement', models.ForeignKey(orm['pr_services.achievement'], null=False)),
            ('to_achievement', models.ForeignKey(orm['pr_services.achievement'], null=False))
        ))
        db.create_unique('pr_services_achievement_component_achievements', ['from_achievement_id', 'to_achievement_id'])

        # Adding model 'AchievementAward'
        db.create_table('pr_services_achievementaward', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('assignment', self.gf('pr_services.fields.PRForeignKey')(related_name='achievement_awards', null=True, to=orm['pr_services.Assignment'])),
            ('user', self.gf('pr_services.fields.PRForeignKey')(related_name='achievement_awards', to=orm['pr_services.User'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('achievement', self.gf('pr_services.fields.PRForeignKey')(related_name='achievement_awards', to=orm['pr_services.Achievement'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('pr_services', ['AchievementAward'])

        # Adding model 'Task'
        db.create_table('pr_services_task', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=191, null=True)),
            ('max', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('public', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('version_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('version_comment', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('version_label', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_tasks', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('prevent_duplicate_assignments', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('pr_services', ['Task'])

        # Adding M2M table for field achievements on 'Task'
        db.create_table('pr_services_task_achievements', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('task', models.ForeignKey(orm['pr_services.task'], null=False)),
            ('achievement', models.ForeignKey(orm['pr_services.achievement'], null=False))
        ))
        db.create_unique('pr_services_task_achievements', ['task_id', 'achievement_id'])

        # Adding M2M table for field prerequisite_tasks on 'Task'
        db.create_table('pr_services_task_prerequisite_tasks', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_task', models.ForeignKey(orm['pr_services.task'], null=False)),
            ('to_task', models.ForeignKey(orm['pr_services.task'], null=False))
        ))
        db.create_unique('pr_services_task_prerequisite_tasks', ['from_task_id', 'to_task_id'])

        # Adding M2M table for field prerequisite_achievements on 'Task'
        db.create_table('pr_services_task_prerequisite_achievements', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('task', models.ForeignKey(orm['pr_services.task'], null=False)),
            ('achievement', models.ForeignKey(orm['pr_services.achievement'], null=False))
        ))
        db.create_unique('pr_services_task_prerequisite_achievements', ['task_id', 'achievement_id'])

        # Adding model 'Curriculum'
        db.create_table('pr_services_curriculum', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('organization', self.gf('pr_services.fields.PRForeignKey')(related_name='curriculums', null=True, to=orm['pr_services.Organization'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['Curriculum'])

        # Adding M2M table for field achievements on 'Curriculum'
        db.create_table('pr_services_curriculum_achievements', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('curriculum', models.ForeignKey(orm['pr_services.curriculum'], null=False)),
            ('achievement', models.ForeignKey(orm['pr_services.achievement'], null=False))
        ))
        db.create_unique('pr_services_curriculum_achievements', ['curriculum_id', 'achievement_id'])

        # Adding model 'CurriculumTaskAssociation'
        db.create_table('pr_services_curriculumtaskassociation', (
            ('task_bundle', self.gf('pr_services.fields.PRForeignKey')(related_name='curriculum_task_associations', null=True, to=orm['pr_services.TaskBundle'])),
            ('task', self.gf('pr_services.fields.PRForeignKey')(related_name='curriculum_task_associations', to=orm['pr_services.Task'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('presentation_order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('curriculum', self.gf('pr_services.fields.PRForeignKey')(related_name='curriculum_task_associations', to=orm['pr_services.Curriculum'])),
            ('days_before_start', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('continue_automatically', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('days_to_complete', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['CurriculumTaskAssociation'])

        # Adding model 'CurriculumEnrollment'
        db.create_table('pr_services_curriculumenrollment', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('curriculum', self.gf('pr_services.fields.PRForeignKey')(related_name='curriculum_enrollments', to=orm['pr_services.Curriculum'])),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end', self.gf('django.db.models.fields.DateField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['CurriculumEnrollment'])

        # Adding model 'CurriculumEnrollmentUserAssociation'
        db.create_table('pr_services_curriculumenrollmentuserassociation', (
            ('curriculum_enrollment', self.gf('pr_services.fields.PRForeignKey')(related_name='curriculum_enrollment_user_associations', to=orm['pr_services.CurriculumEnrollment'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('user', self.gf('pr_services.fields.PRForeignKey')(related_name='curriculum_enrollment_user_associations', to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('pr_services', ['CurriculumEnrollmentUserAssociation'])

        # Adding model 'Assignment'
        db.create_table('pr_services_assignment', (
            ('status', self.gf('django.db.models.fields.CharField')(default='assigned', max_length=16, db_index=True)),
            ('due_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('task', self.gf('pr_services.fields.PRForeignKey')(related_name='assignments', to=orm['pr_services.Task'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('sent_reminder', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('curriculum_enrollment', self.gf('pr_services.fields.PRForeignKey')(related_name='assignments', null=True, to=orm['pr_services.CurriculumEnrollment'])),
            ('product_claim', self.gf('pr_services.fields.PRForeignKey')(related_name='assignments', null=True, to=orm['pr_services.ProductClaim'])),
            ('sent_confirmation', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('authority', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='assignments', null=True, to=orm['pr_services.Blame'])),
            ('effective_date_assigned', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('user', self.gf('pr_services.fields.PRForeignKey')(related_name='assignments', to=orm['pr_services.User'])),
            ('serial_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('sent_pre_reminder', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('date_completed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('date_started', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('sent_late_notice', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('pr_services', ['Assignment'])

        # Adding model 'AssignmentAttempt'
        db.create_table('pr_services_assignmentattempt', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('assignment', self.gf('pr_services.fields.PRForeignKey')(related_name='assignment_attempts', to=orm['pr_services.Assignment'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_assignmentattempts', null=True, to=orm['pr_services.User'])),
            ('date_completed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('date_started', self.gf('django.db.models.fields.DateTimeField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['AssignmentAttempt'])

        # Adding model 'TaskBundle'
        db.create_table('pr_services_taskbundle', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('organization', self.gf('pr_services.fields.PRForeignKey')(related_name='task_bundles', null=True, to=orm['pr_services.Organization'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('pr_services', ['TaskBundle'])

        # Adding model 'TaskBundleTaskAssociation'
        db.create_table('pr_services_taskbundletaskassociation', (
            ('task_bundle', self.gf('pr_services.fields.PRForeignKey')(related_name='task_bundle_task_associations', to=orm['pr_services.TaskBundle'])),
            ('task', self.gf('pr_services.fields.PRForeignKey')(related_name='task_bundle_task_associations', to=orm['pr_services.Task'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('presentation_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('continue_automatically', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['TaskBundleTaskAssociation'])

        # Adding model 'ProductLine'
        db.create_table('pr_services_productline', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_productlines', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['ProductLine'])

        # Adding M2M table for field instructors on 'ProductLine'
        db.create_table('pr_services_productline_instructors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productline', models.ForeignKey(orm['pr_services.productline'], null=False)),
            ('user', models.ForeignKey(orm['pr_services.user'], null=False))
        ))
        db.create_unique('pr_services_productline_instructors', ['productline_id', 'user_id'])

        # Adding M2M table for field notes on 'ProductLine'
        db.create_table('pr_services_productline_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productline', models.ForeignKey(orm['pr_services.productline'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_productline_notes', ['productline_id', 'note_id'])

        # Adding M2M table for field instructor_managers on 'ProductLine'
        db.create_table('pr_services_productline_instructor_managers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productline', models.ForeignKey(orm['pr_services.productline'], null=False)),
            ('user', models.ForeignKey(orm['pr_services.user'], null=False))
        ))
        db.create_unique('pr_services_productline_instructor_managers', ['productline_id', 'user_id'])

        # Adding M2M table for field managers on 'ProductLine'
        db.create_table('pr_services_productline_managers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productline', models.ForeignKey(orm['pr_services.productline'], null=False)),
            ('user', models.ForeignKey(orm['pr_services.user'], null=False))
        ))
        db.create_unique('pr_services_productline_managers', ['productline_id', 'user_id'])

        # Adding model 'Region'
        db.create_table('pr_services_region', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_regions', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['Region'])

        # Adding M2M table for field notes on 'Region'
        db.create_table('pr_services_region_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('region', models.ForeignKey(orm['pr_services.region'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_region_notes', ['region_id', 'note_id'])

        # Adding model 'Resource'
        db.create_table('pr_services_resource', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_resources', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['Resource'])

        # Adding M2M table for field notes on 'Resource'
        db.create_table('pr_services_resource_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('resource', models.ForeignKey(orm['pr_services.resource'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_resource_notes', ['resource_id', 'note_id'])

        # Adding model 'Group'
        db.create_table('pr_services_group', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('default', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_groups', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['Group'])

        # Adding M2M table for field notes on 'Group'
        db.create_table('pr_services_group_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['pr_services.group'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_group_notes', ['group_id', 'note_id'])

        # Adding M2M table for field managers on 'Group'
        db.create_table('pr_services_group_managers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['pr_services.group'], null=False)),
            ('user', models.ForeignKey(orm['pr_services.user'], null=False))
        ))
        db.create_unique('pr_services_group_managers', ['group_id', 'user_id'])

        # Adding model 'Role'
        db.create_table('pr_services_role', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_roles', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['Role'])

        # Adding M2M table for field notes on 'Role'
        db.create_table('pr_services_role_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('role', models.ForeignKey(orm['pr_services.role'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_role_notes', ['role_id', 'note_id'])

        # Adding model 'ACL'
        db.create_table('pr_services_acl', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('arbitrary_perm_list', self.gf('django.db.models.fields.TextField')()),
            ('acl', self.gf('django.db.models.fields.TextField')()),
            ('role', self.gf('pr_services.fields.PRForeignKey')(related_name='acls', to=orm['pr_services.Role'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_acls', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['ACL'])

        # Adding model 'ACCheckMethod'
        db.create_table('pr_services_accheckmethod', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128, unique=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_accheckmethods', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['ACCheckMethod'])

        # Adding model 'ACMethodCall'
        db.create_table('pr_services_acmethodcall', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('acl', self.gf('pr_services.fields.PRForeignKey')(related_name='ac_method_calls', to=orm['pr_services.ACL'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_acmethodcalls', null=True, to=orm['pr_services.User'])),
            ('ac_check_method', self.gf('pr_services.fields.PRForeignKey')(related_name='ac_method_calls', to=orm['pr_services.ACCheckMethod'])),
            ('ac_check_parameters', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['ACMethodCall'])

        # Adding model 'Address'
        db.create_table('pr_services_address', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('locality', self.gf('django.db.models.fields.CharField')(default='', max_length=31, null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('region', self.gf('django.db.models.fields.CharField')(default='', max_length=31, null=True, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(default='', max_length=16, null=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_addresss', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['Address'])

        # Adding model 'Domain'
        db.create_table('pr_services_domain', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('password_hash_type', self.gf('django.db.models.fields.CharField')(default='SHA-512', max_length=8)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('authentication_ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True)),
            ('authentication_password_hash', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
        ))
        db.send_create_signal('pr_services', ['Domain'])

        # Adding model 'DomainAffiliation'
        db.create_table('pr_services_domainaffiliation', (
            ('username', self.gf('django.db.models.fields.CharField')(max_length=31, db_index=True)),
            ('domain', self.gf('pr_services.fields.PRForeignKey')(related_name='domain_affiliations', to=orm['pr_services.Domain'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('password_salt', self.gf('django.db.models.fields.CharField')(max_length=8, null=True)),
            ('default', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('user', self.gf('pr_services.fields.PRForeignKey')(related_name='domain_affiliations', to=orm['pr_services.User'])),
            ('password_hash_type', self.gf('django.db.models.fields.CharField')(default='SHA-512', max_length=8)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('may_log_me_in', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password_hash', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('pr_services', ['DomainAffiliation'])

        # Adding unique constraint on 'DomainAffiliation', fields ['username', 'domain']
        db.create_unique('pr_services_domainaffiliation', ['username', 'domain_id'])

        # Adding model 'User'
        db.create_table('pr_services_user', (
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True)),
            ('is_staff', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_users', null=True, to=orm['pr_services.User'])),
            ('email2', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('biography', self.gf('django.db.models.fields.TextField')(null=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('middle_name', self.gf('django.db.models.fields.CharField')(default='', max_length=31)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('confirmation_code', self.gf('django.db.models.fields.CharField')(max_length=40, null=True)),
            ('enable_paypal', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('billing_address', self.gf('pr_services.fields.PRForeignKey')(related_name='users_billing', null=True, to=orm['pr_services.Address'])),
            ('color_code', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('phone2', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('phone3', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='created_users', null=True, to=orm['pr_services.Blame'])),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
            ('name_suffix', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('suppress_emails', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('alleged_organization', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('paypal_address', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True)),
            ('shipping_address', self.gf('pr_services.fields.PRForeignKey')(related_name='users_shipping', null=True, to=orm['pr_services.Address'])),
        ))
        db.send_create_signal('pr_services', ['User'])

        # Adding M2M table for field notes on 'User'
        db.create_table('pr_services_user_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm['pr_services.user'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_user_notes', ['user_id', 'note_id'])

        # Adding M2M table for field groups on 'User'
        db.create_table('pr_services_user_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm['pr_services.user'], null=False)),
            ('group', models.ForeignKey(orm['pr_services.group'], null=False))
        ))
        db.create_unique('pr_services_user_groups', ['user_id', 'group_id'])

        # Adding M2M table for field preferred_venues on 'User'
        db.create_table('pr_services_user_preferred_venues', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm['pr_services.user'], null=False)),
            ('venue', models.ForeignKey(orm['pr_services.venue'], null=False))
        ))
        db.create_unique('pr_services_user_preferred_venues', ['user_id', 'venue_id'])

        # Adding model 'Blame'
        db.create_table('pr_services_blame', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('user', self.gf('pr_services.fields.PRForeignKey')(related_name='blamed_user', to=orm['pr_services.User'])),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_blames', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('pr_services', ['Blame'])

        # Adding model 'SessionTemplate'
        db.create_table('pr_services_sessiontemplate', (
            ('product_line', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.ProductLine'], null=True)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('sequence', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('price', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('event_template', self.gf('pr_services.fields.PRForeignKey')(related_name='session_templates', null=True, to=orm['pr_services.EventTemplate'])),
            ('fullname', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('modality', self.gf('django.db.models.fields.CharField')(default='Generic', max_length=31)),
            ('duration', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('audience', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_sessiontemplates', null=True, to=orm['pr_services.User'])),
            ('shortname', self.gf('django.db.models.fields.CharField')(max_length=31, unique=True)),
            ('lead_time', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('pr_services', ['SessionTemplate'])

        # Adding M2M table for field notes on 'SessionTemplate'
        db.create_table('pr_services_sessiontemplate_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessiontemplate', models.ForeignKey(orm['pr_services.sessiontemplate'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_sessiontemplate_notes', ['sessiontemplate_id', 'note_id'])

        # Adding model 'Venue'
        db.create_table('pr_services_venue', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('region', self.gf('pr_services.fields.PRForeignKey')(related_name='venues', to=orm['pr_services.Region'])),
            ('hours_of_operation', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('contact', self.gf('django.db.models.fields.CharField')(max_length=63, null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('address', self.gf('pr_services.fields.PRForeignKey')(related_name='venues', null=True, to=orm['pr_services.Address'])),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_venues', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('pr_services', ['Venue'])

        # Adding M2M table for field notes on 'Venue'
        db.create_table('pr_services_venue_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('venue', models.ForeignKey(orm['pr_services.venue'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_venue_notes', ['venue_id', 'note_id'])

        # Adding model 'Room'
        db.create_table('pr_services_room', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('room_number', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('venue', self.gf('pr_services.fields.PRForeignKey')(related_name='rooms', to=orm['pr_services.Venue'])),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_rooms', null=True, to=orm['pr_services.User'])),
            ('capacity', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=63)),
        ))
        db.send_create_signal('pr_services', ['Room'])

        # Adding M2M table for field notes on 'Room'
        db.create_table('pr_services_room_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('room', models.ForeignKey(orm['pr_services.room'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_room_notes', ['room_id', 'note_id'])

        # Adding model 'Session'
        db.create_table('pr_services_session', (
            ('default_price', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_sessions', null=True, to=orm['pr_services.User'])),
            ('sent_reminders', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('modality', self.gf('django.db.models.fields.CharField')(default='Generic', max_length=31)),
            ('confirmed', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
            ('session_template', self.gf('pr_services.fields.PRForeignKey')(related_name='sessions', null=True, to=orm['pr_services.SessionTemplate'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=127, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('evaluation', self.gf('pr_services.fields.PROneToOneField')(related_name='session', unique=True, null=True, to=orm['pr_services.Exam'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('graphic', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('room', self.gf('pr_services.fields.PRForeignKey')(related_name='sessions', null=True, to=orm['pr_services.Room'])),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=255, null=True)),
            ('event', self.gf('pr_services.fields.PRForeignKey')(related_name='sessions', to=orm['pr_services.Event'])),
            ('audience', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
        ))
        db.send_create_signal('pr_services', ['Session'])

        # Adding M2M table for field notes on 'Session'
        db.create_table('pr_services_session_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('session', models.ForeignKey(orm['pr_services.session'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_session_notes', ['session_id', 'note_id'])

        # Adding model 'EventTemplate'
        db.create_table('pr_services_eventtemplate', (
            ('product_line', self.gf('pr_services.fields.PRForeignKey')(related_name='event_templates', null=True, to=orm['pr_services.ProductLine'])),
            ('name_prefix', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('twitter_template', self.gf('django.db.models.fields.CharField')(default='I just signed up for {{event}}! Join me! {{url}}', max_length=255)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=127, null=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=255, null=True)),
            ('facebook_template', self.gf('django.db.models.fields.CharField')(default='I just signed up for {{event}}! Click the link to join me.', max_length=255)),
            ('external_reference', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('lag_time', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_eventtemplates', null=True, to=orm['pr_services.User'])),
            ('organization', self.gf('pr_services.fields.PRForeignKey')(related_name='event_templates', null=True, to=orm['pr_services.Organization'])),
            ('lead_time', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['EventTemplate'])

        # Adding M2M table for field notes on 'EventTemplate'
        db.create_table('pr_services_eventtemplate_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('eventtemplate', models.ForeignKey(orm['pr_services.eventtemplate'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_eventtemplate_notes', ['eventtemplate_id', 'note_id'])

        # Adding model 'Event'
        db.create_table('pr_services_event', (
            ('product_line', self.gf('pr_services.fields.PRForeignKey')(related_name='events', to=orm['pr_services.ProductLine'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('twitter_template', self.gf('django.db.models.fields.CharField')(default='I just signed up for {{event}}! Join me! {{url}}', max_length=255)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=127, null=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=255, null=True)),
            ('facebook_template', self.gf('django.db.models.fields.CharField')(default='I just signed up for {{event}}! Click the link to join me.', max_length=255)),
            ('region', self.gf('pr_services.fields.PRForeignKey')(related_name='events', null=True, to=orm['pr_services.Region'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('venue', self.gf('pr_services.fields.PRForeignKey')(related_name='events', null=True, to=orm['pr_services.Venue'])),
            ('external_reference', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('event_template', self.gf('pr_services.fields.PRForeignKey')(related_name='events', null=True, to=orm['pr_services.EventTemplate'])),
            ('lag_time', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('organization', self.gf('pr_services.fields.PRForeignKey')(related_name='events', to=orm['pr_services.Organization'])),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_events', null=True, to=orm['pr_services.User'])),
            ('end', self.gf('django.db.models.fields.DateField')()),
            ('lead_time', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['Event'])

        # Adding M2M table for field notes on 'Event'
        db.create_table('pr_services_event_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('event', models.ForeignKey(orm['pr_services.event'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_event_notes', ['event_id', 'note_id'])

        # Adding model 'SessionUserRole'
        db.create_table('pr_services_sessionuserrole', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_sessionuserroles', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['SessionUserRole'])

        # Adding M2M table for field notes on 'SessionUserRole'
        db.create_table('pr_services_sessionuserrole_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessionuserrole', models.ForeignKey(orm['pr_services.sessionuserrole'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_sessionuserrole_notes', ['sessionuserrole_id', 'note_id'])

        # Adding model 'ResourceType'
        db.create_table('pr_services_resourcetype', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_resourcetypes', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['ResourceType'])

        # Adding M2M table for field notes on 'ResourceType'
        db.create_table('pr_services_resourcetype_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('resourcetype', models.ForeignKey(orm['pr_services.resourcetype'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_resourcetype_notes', ['resourcetype_id', 'note_id'])

        # Adding M2M table for field resources on 'ResourceType'
        db.create_table('pr_services_resourcetype_resources', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('resourcetype', models.ForeignKey(orm['pr_services.resourcetype'], null=False)),
            ('resource', models.ForeignKey(orm['pr_services.resource'], null=False))
        ))
        db.create_unique('pr_services_resourcetype_resources', ['resourcetype_id', 'resource_id'])

        # Adding model 'SessionUserRoleRequirement'
        db.create_table('pr_services_sessionuserrolerequirement', (
            ('task_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pr_services.Task'], unique=True, primary_key=True)),
            ('enrollment_status_test', self.gf('pr_services.fields.PRForeignKey')(related_name='session_user_role_requirements', null=True, to=orm['pr_services.ConditionTestCollection'])),
            ('session', self.gf('pr_services.fields.PRForeignKey')(related_name='session_user_role_requirements', to=orm['pr_services.Session'])),
            ('session_user_role', self.gf('pr_services.fields.PRForeignKey')(related_name='session_user_role_requirements', to=orm['pr_services.SessionUserRole'])),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('ignore_room_capacity', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('pr_services', ['SessionUserRoleRequirement'])

        # Adding M2M table for field credential_types on 'SessionUserRoleRequirement'
        db.create_table('pr_services_sessionuserrolerequirement_credential_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessionuserrolerequirement', models.ForeignKey(orm['pr_services.sessionuserrolerequirement'], null=False)),
            ('credentialtype', models.ForeignKey(orm['pr_services.credentialtype'], null=False))
        ))
        db.create_unique('pr_services_sessionuserrolerequirement_credential_types', ['sessionuserrolerequirement_id', 'credentialtype_id'])

        # Adding M2M table for field notes on 'SessionUserRoleRequirement'
        db.create_table('pr_services_sessionuserrolerequirement_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessionuserrolerequirement', models.ForeignKey(orm['pr_services.sessionuserrolerequirement'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_sessionuserrolerequirement_notes', ['sessionuserrolerequirement_id', 'note_id'])

        # Adding model 'SessionTemplateUserRoleReq'
        db.create_table('pr_services_sessiontemplateuserrolereq', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('min', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('max', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('session_user_role', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.SessionUserRole'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_sessiontemplateuserrolereqs', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session_template', self.gf('pr_services.fields.PRForeignKey')(related_name='session_template_user_role_requirements', to=orm['pr_services.SessionTemplate'])),
        ))
        db.send_create_signal('pr_services', ['SessionTemplateUserRoleReq'])

        # Adding M2M table for field notes on 'SessionTemplateUserRoleReq'
        db.create_table('pr_services_sessiontemplateuserrolereq_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessiontemplateuserrolereq', models.ForeignKey(orm['pr_services.sessiontemplateuserrolereq'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_sessiontemplateuserrolereq_notes', ['sessiontemplateuserrolereq_id', 'note_id'])

        # Adding model 'AuthToken'
        db.create_table('pr_services_authtoken', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('time_of_expiration', self.gf('django.db.models.fields.DateTimeField')()),
            ('issue_timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('number_of_renewals', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=32, unique=True, db_index=True)),
            ('renewal_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(default='0.0.0.0', max_length=15)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_authtokens', null=True, to=orm['pr_services.User'])),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain_affiliation', self.gf('pr_services.fields.PRForeignKey')(related_name='auth_tokens', to=orm['pr_services.DomainAffiliation'])),
        ))
        db.send_create_signal('pr_services', ['AuthToken'])

        # Adding model 'SingleUseAuthToken'
        db.create_table('pr_services_singleuseauthtoken', (
            ('used', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('authtoken_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pr_services.AuthToken'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['SingleUseAuthToken'])

        # Adding model 'AuthTokenVoucher'
        db.create_table('pr_services_authtokenvoucher', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('time_of_expiration', self.gf('django.db.models.fields.DateTimeField')()),
            ('issue_timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=32, unique=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_authtokenvouchers', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain_affiliation', self.gf('pr_services.fields.PRForeignKey')(related_name='auth_token_vouchers', to=orm['pr_services.DomainAffiliation'])),
        ))
        db.send_create_signal('pr_services', ['AuthTokenVoucher'])

        # Adding model 'SessionTemplateResourceTypeReq'
        db.create_table('pr_services_sessiontemplateresourcetypereq', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('min', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('max', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_sessiontemplateresourcetypereqs', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resource_type', self.gf('pr_services.fields.PRForeignKey')(related_name='sessiontemplateresourcetypereqs', to=orm['pr_services.ResourceType'])),
            ('session_template', self.gf('pr_services.fields.PRForeignKey')(related_name='session_template_resource_type_requirements', to=orm['pr_services.SessionTemplate'])),
        ))
        db.send_create_signal('pr_services', ['SessionTemplateResourceTypeReq'])

        # Adding M2M table for field notes on 'SessionTemplateResourceTypeReq'
        db.create_table('pr_services_sessiontemplateresourcetypereq_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessiontemplateresourcetypereq', models.ForeignKey(orm['pr_services.sessiontemplateresourcetypereq'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_sessiontemplateresourcetypereq_notes', ['sessiontemplateresourcetypereq_id', 'note_id'])

        # Adding model 'SessionResourceTypeRequirement'
        db.create_table('pr_services_sessionresourcetyperequirement', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('min', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('max', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('session', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Session'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_sessionresourcetyperequirements', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resource_type', self.gf('pr_services.fields.PRForeignKey')(related_name='sessionresourcetyperequirements', to=orm['pr_services.ResourceType'])),
        ))
        db.send_create_signal('pr_services', ['SessionResourceTypeRequirement'])

        # Adding M2M table for field notes on 'SessionResourceTypeRequirement'
        db.create_table('pr_services_sessionresourcetyperequirement_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessionresourcetyperequirement', models.ForeignKey(orm['pr_services.sessionresourcetyperequirement'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_sessionresourcetyperequirement_notes', ['sessionresourcetyperequirement_id', 'note_id'])

        # Adding M2M table for field resources on 'SessionResourceTypeRequirement'
        db.create_table('pr_services_sessionresourcetyperequirement_resources', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sessionresourcetyperequirement', models.ForeignKey(orm['pr_services.sessionresourcetyperequirement'], null=False)),
            ('resource', models.ForeignKey(orm['pr_services.resource'], null=False))
        ))
        db.create_unique('pr_services_sessionresourcetyperequirement_resources', ['sessionresourcetyperequirement_id', 'resource_id'])

        # Adding model 'PurchaseOrder'
        db.create_table('pr_services_purchaseorder', (
            ('training_units_price', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('expiration', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('training_units_purchased', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('promo_code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_purchaseorders', null=True, to=orm['pr_services.User'])),
            ('organization', self.gf('pr_services.fields.PRForeignKey')(related_name='purchase_orders', null=True, to=orm['pr_services.Organization'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.User'], null=True)),
        ))
        db.send_create_signal('pr_services', ['PurchaseOrder'])

        # Adding M2M table for field product_discounts on 'PurchaseOrder'
        db.create_table('pr_services_purchaseorder_product_discounts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('purchaseorder', models.ForeignKey(orm['pr_services.purchaseorder'], null=False)),
            ('productdiscount', models.ForeignKey(orm['pr_services.productdiscount'], null=False))
        ))
        db.create_unique('pr_services_purchaseorder_product_discounts', ['purchaseorder_id', 'productdiscount_id'])

        # Adding M2M table for field notes on 'PurchaseOrder'
        db.create_table('pr_services_purchaseorder_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('purchaseorder', models.ForeignKey(orm['pr_services.purchaseorder'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_purchaseorder_notes', ['purchaseorder_id', 'note_id'])

        # Adding model 'TrainingUnitAccount'
        db.create_table('pr_services_trainingunitaccount', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_trainingunitaccounts', null=True, to=orm['pr_services.User'])),
            ('organization', self.gf('pr_services.fields.PRForeignKey')(related_name='trainingunitaccounts', null=True, to=orm['pr_services.Organization'])),
            ('starting_value', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.User'], null=True)),
        ))
        db.send_create_signal('pr_services', ['TrainingUnitAccount'])

        # Adding M2M table for field notes on 'TrainingUnitAccount'
        db.create_table('pr_services_trainingunitaccount_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('trainingunitaccount', models.ForeignKey(orm['pr_services.trainingunitaccount'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_trainingunitaccount_notes', ['trainingunitaccount_id', 'note_id'])

        # Adding model 'TrainingUnitTransaction'
        db.create_table('pr_services_trainingunittransaction', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('purchase_order', self.gf('pr_services.fields.PRForeignKey')(related_name='training_unit_transactions', to=orm['pr_services.PurchaseOrder'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_trainingunittransactions', null=True, to=orm['pr_services.User'])),
            ('training_unit_account', self.gf('pr_services.fields.PRForeignKey')(related_name='training_unit_transactions', to=orm['pr_services.TrainingUnitAccount'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['TrainingUnitTransaction'])

        # Adding M2M table for field notes on 'TrainingUnitTransaction'
        db.create_table('pr_services_trainingunittransaction_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('trainingunittransaction', models.ForeignKey(orm['pr_services.trainingunittransaction'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_trainingunittransaction_notes', ['trainingunittransaction_id', 'note_id'])

        # Adding model 'TrainingUnitAuthorization'
        db.create_table('pr_services_trainingunitauthorization', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('max_value', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_trainingunitauthorizations', null=True, to=orm['pr_services.User'])),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
            ('training_unit_account', self.gf('pr_services.fields.PRForeignKey')(related_name='training_unit_authorizations', to=orm['pr_services.TrainingUnitAccount'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('pr_services.fields.PRForeignKey')(related_name='training_unit_authorizations', to=orm['pr_services.User'])),
        ))
        db.send_create_signal('pr_services', ['TrainingUnitAuthorization'])

        # Adding M2M table for field notes on 'TrainingUnitAuthorization'
        db.create_table('pr_services_trainingunitauthorization_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('trainingunitauthorization', models.ForeignKey(orm['pr_services.trainingunitauthorization'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_trainingunitauthorization_notes', ['trainingunitauthorization_id', 'note_id'])

        # Adding M2M table for field transactions on 'TrainingUnitAuthorization'
        db.create_table('pr_services_trainingunitauthorization_transactions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('trainingunitauthorization', models.ForeignKey(orm['pr_services.trainingunitauthorization'], null=False)),
            ('trainingunittransaction', models.ForeignKey(orm['pr_services.trainingunittransaction'], null=False))
        ))
        db.create_unique('pr_services_trainingunitauthorization_transactions', ['trainingunitauthorization_id', 'trainingunittransaction_id'])

        # Adding model 'TrainingVoucher'
        db.create_table('pr_services_trainingvoucher', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('purchase_order', self.gf('pr_services.fields.PRForeignKey')(related_name='training_vouchers', null=True, to=orm['pr_services.PurchaseOrder'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_trainingvouchers', null=True, to=orm['pr_services.User'])),
            ('session_user_role_requirement', self.gf('pr_services.fields.PRForeignKey')(related_name='training_vouchers', to=orm['pr_services.SessionUserRoleRequirement'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['TrainingVoucher'])

        # Adding M2M table for field notes on 'TrainingVoucher'
        db.create_table('pr_services_trainingvoucher_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('trainingvoucher', models.ForeignKey(orm['pr_services.trainingvoucher'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_trainingvoucher_notes', ['trainingvoucher_id', 'note_id'])

        # Adding model 'Payment'
        db.create_table('pr_services_payment', (
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('exp_date', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_payments', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('purchase_order', self.gf('pr_services.fields.PRForeignKey')(related_name='payments', to=orm['pr_services.PurchaseOrder'])),
            ('address_label', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('result_message', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('transaction_id', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('invoice_number', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('card_type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('sales_tax', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('card_number', self.gf('django.db.models.fields.CharField')(max_length=16)),
        ))
        db.send_create_signal('pr_services', ['Payment'])

        # Adding M2M table for field notes on 'Payment'
        db.create_table('pr_services_payment_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('payment', models.ForeignKey(orm['pr_services.payment'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_payment_notes', ['payment_id', 'note_id'])

        # Adding model 'Refund'
        db.create_table('pr_services_refund', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('result_message', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('payment', self.gf('pr_services.fields.PRForeignKey')(related_name='refunds', to=orm['pr_services.Payment'])),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.Blame'], null=True)),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_refunds', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('transaction_id', self.gf('django.db.models.fields.CharField')(max_length=63)),
        ))
        db.send_create_signal('pr_services', ['Refund'])

        # Adding model 'CSVData'
        db.create_table('pr_services_csvdata', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_csvdatas', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.User'])),
        ))
        db.send_create_signal('pr_services', ['CSVData'])

        # Adding model 'Product'
        db.create_table('pr_services_product', (
            ('sku', self.gf('django.db.models.fields.CharField')(max_length=32, unique=True)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('display_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True)),
            ('starting_quantity', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='products', null=True, to=orm['pr_services.Blame'])),
            ('cost', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('visibility_condition_test_collection', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.ConditionTestCollection'], null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_products', null=True, to=orm['pr_services.User'])),
            ('training_units', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('price', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('pr_services', ['Product'])

        # Adding M2M table for field notes on 'Product'
        db.create_table('pr_services_product_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('product', models.ForeignKey(orm['pr_services.product'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_product_notes', ['product_id', 'note_id'])

        # Adding M2M table for field custom_actions on 'Product'
        db.create_table('pr_services_product_custom_actions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('product', models.ForeignKey(orm['pr_services.product'], null=False)),
            ('customaction', models.ForeignKey(orm['pr_services.customaction'], null=False))
        ))
        db.create_unique('pr_services_product_custom_actions', ['product_id', 'customaction_id'])

        # Adding model 'TaskFee'
        db.create_table('pr_services_taskfee', (
            ('task', self.gf('pr_services.fields.PRForeignKey')(related_name='task_fees', to=orm['pr_services.Task'])),
            ('product_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pr_services.Product'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['TaskFee'])

        # Adding model 'ProductClaim'
        db.create_table('pr_services_productclaim', (
            ('product', self.gf('pr_services.fields.PRForeignKey')(related_name='product_claims', to=orm['pr_services.Product'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('discounts_searched', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='product_claims', null=True, to=orm['pr_services.Blame'])),
            ('purchase_order', self.gf('pr_services.fields.PRForeignKey')(related_name='product_claims', to=orm['pr_services.PurchaseOrder'])),
            ('training_units_paid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_productclaims', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('price_paid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('quantity', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
        ))
        db.send_create_signal('pr_services', ['ProductClaim'])

        # Adding M2M table for field discounts on 'ProductClaim'
        db.create_table('pr_services_productclaim_discounts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productclaim', models.ForeignKey(orm['pr_services.productclaim'], null=False)),
            ('productdiscount', models.ForeignKey(orm['pr_services.productdiscount'], null=False))
        ))
        db.create_unique('pr_services_productclaim_discounts', ['productclaim_id', 'productdiscount_id'])

        # Adding model 'ClaimProductOffers'
        db.create_table('pr_services_claimproductoffers', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('purchase_order', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.PurchaseOrder'])),
            ('training_units_paid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_claimproductofferss', null=True, to=orm['pr_services.User'])),
            ('quantity', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('price_paid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('product_offer', self.gf('pr_services.fields.PRForeignKey')(to=orm['pr_services.ProductOffer'])),
        ))
        db.send_create_signal('pr_services', ['ClaimProductOffers'])

        # Adding M2M table for field discounts on 'ClaimProductOffers'
        db.create_table('pr_services_claimproductoffers_discounts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('claimproductoffers', models.ForeignKey(orm['pr_services.claimproductoffers'], null=False)),
            ('productdiscount', models.ForeignKey(orm['pr_services.productdiscount'], null=False))
        ))
        db.create_unique('pr_services_claimproductoffers_discounts', ['claimproductoffers_id', 'productdiscount_id'])

        # Adding model 'ProductTransaction'
        db.create_table('pr_services_producttransaction', (
            ('product', self.gf('pr_services.fields.PRForeignKey')(related_name='product_transactions', to=orm['pr_services.Product'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='product_transactions', null=True, to=orm['pr_services.Blame'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_producttransactions', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('change', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('pr_services', ['ProductTransaction'])

        # Adding model 'ProductDiscount'
        db.create_table('pr_services_productdiscount', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('currency', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('condition_test_collection', self.gf('pr_services.fields.PRForeignKey')(related_name='product_discounts', null=True, to=orm['pr_services.ConditionTestCollection'])),
            ('cumulative', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=63, null=True)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='product_discounts', null=True, to=orm['pr_services.Blame'])),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_productdiscounts', null=True, to=orm['pr_services.User'])),
            ('training_units', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('percentage', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('promo_code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
        ))
        db.send_create_signal('pr_services', ['ProductDiscount'])

        # Adding M2M table for field notes on 'ProductDiscount'
        db.create_table('pr_services_productdiscount_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productdiscount', models.ForeignKey(orm['pr_services.productdiscount'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_productdiscount_notes', ['productdiscount_id', 'note_id'])

        # Adding M2M table for field product_offers on 'ProductDiscount'
        db.create_table('pr_services_productdiscount_product_offers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productdiscount', models.ForeignKey(orm['pr_services.productdiscount'], null=False)),
            ('productoffer', models.ForeignKey(orm['pr_services.productoffer'], null=False))
        ))
        db.create_unique('pr_services_productdiscount_product_offers', ['productdiscount_id', 'productoffer_id'])

        # Adding M2M table for field products on 'ProductDiscount'
        db.create_table('pr_services_productdiscount_products', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productdiscount', models.ForeignKey(orm['pr_services.productdiscount'], null=False)),
            ('product', models.ForeignKey(orm['pr_services.product'], null=False))
        ))
        db.create_unique('pr_services_productdiscount_products', ['productdiscount_id', 'product_id'])

        # Adding model 'ProductOffer'
        db.create_table('pr_services_productoffer', (
            ('product', self.gf('pr_services.fields.PRForeignKey')(related_name='product_offers', to=orm['pr_services.Product'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('price', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('seller', self.gf('pr_services.fields.PRForeignKey')(related_name='product_offers', to=orm['pr_services.User'])),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='product_offers', null=True, to=orm['pr_services.Blame'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_productoffers', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('pr_services', ['ProductOffer'])

        # Adding M2M table for field notes on 'ProductOffer'
        db.create_table('pr_services_productoffer_notes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productoffer', models.ForeignKey(orm['pr_services.productoffer'], null=False)),
            ('note', models.ForeignKey(orm['pr_services.note'], null=False))
        ))
        db.create_unique('pr_services_productoffer_notes', ['productoffer_id', 'note_id'])

        # Adding model 'ConditionTestCollection'
        db.create_table('pr_services_conditiontestcollection', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='condition_test_collections', null=True, to=orm['pr_services.Blame'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['ConditionTestCollection'])

        # Adding model 'ConditionTest'
        db.create_table('pr_services_conditiontest', (
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='condition_tests', to=orm['pr_services.Blame'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('sequence', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('condition_test_collection', self.gf('pr_services.fields.PRForeignKey')(related_name='condition_tests', to=orm['pr_services.ConditionTestCollection'])),
            ('match_all_defined_parameters', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['ConditionTest'])

        # Adding M2M table for field organizations on 'ConditionTest'
        db.create_table('pr_services_conditiontest_organizations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('conditiontest', models.ForeignKey(orm['pr_services.conditiontest'], null=False)),
            ('organization', models.ForeignKey(orm['pr_services.organization'], null=False))
        ))
        db.create_unique('pr_services_conditiontest_organizations', ['conditiontest_id', 'organization_id'])

        # Adding M2M table for field session_user_role_requirements on 'ConditionTest'
        db.create_table('pr_services_conditiontest_session_user_role_requirements', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('conditiontest', models.ForeignKey(orm['pr_services.conditiontest'], null=False)),
            ('sessionuserrolerequirement', models.ForeignKey(orm['pr_services.sessionuserrolerequirement'], null=False))
        ))
        db.create_unique('pr_services_conditiontest_session_user_role_requirements', ['conditiontest_id', 'sessionuserrolerequirement_id'])

        # Adding M2M table for field sessions on 'ConditionTest'
        db.create_table('pr_services_conditiontest_sessions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('conditiontest', models.ForeignKey(orm['pr_services.conditiontest'], null=False)),
            ('session', models.ForeignKey(orm['pr_services.session'], null=False))
        ))
        db.create_unique('pr_services_conditiontest_sessions', ['conditiontest_id', 'session_id'])

        # Adding M2M table for field groups on 'ConditionTest'
        db.create_table('pr_services_conditiontest_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('conditiontest', models.ForeignKey(orm['pr_services.conditiontest'], null=False)),
            ('group', models.ForeignKey(orm['pr_services.group'], null=False))
        ))
        db.create_unique('pr_services_conditiontest_groups', ['conditiontest_id', 'group_id'])

        # Adding M2M table for field credentials on 'ConditionTest'
        db.create_table('pr_services_conditiontest_credentials', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('conditiontest', models.ForeignKey(orm['pr_services.conditiontest'], null=False)),
            ('credential', models.ForeignKey(orm['pr_services.credential'], null=False))
        ))
        db.create_unique('pr_services_conditiontest_credentials', ['conditiontest_id', 'credential_id'])

        # Adding M2M table for field events on 'ConditionTest'
        db.create_table('pr_services_conditiontest_events', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('conditiontest', models.ForeignKey(orm['pr_services.conditiontest'], null=False)),
            ('event', models.ForeignKey(orm['pr_services.event'], null=False))
        ))
        db.create_unique('pr_services_conditiontest_events', ['conditiontest_id', 'event_id'])

        # Adding model 'Course'
        db.create_table('pr_services_course', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_courses', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['Course'])

        # Adding model 'Sco'
        db.create_table('pr_services_sco', (
            ('task_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pr_services.Task'], unique=True, primary_key=True)),
            ('course', self.gf('pr_services.fields.PRForeignKey')(related_name='scos', to=orm['pr_services.Course'])),
            ('completion_requirement', self.gf('django.db.models.fields.CharField')(default='visit_sco', max_length=64)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('data', self.gf('django.db.models.fields.CharField')(max_length=1024)),
        ))
        db.send_create_signal('pr_services', ['Sco'])

        # Adding model 'ScoSession'
        db.create_table('pr_services_scosession', (
            ('cmi_core_score_max', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('cmi_core_score_min', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('shared_object', self.gf('django.db.models.fields.TextField')()),
            ('cmi_core_lesson_status', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('assignmentattempt_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pr_services.AssignmentAttempt'], unique=True, primary_key=True)),
            ('cmi_core_lesson_location', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
        ))
        db.send_create_signal('pr_services', ['ScoSession'])

        # Adding model 'CachedCookie'
        db.create_table('pr_services_cachedcookie', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('value', self.gf('django.db.models.fields.TextField')()),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_cachedcookies', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['CachedCookie'])

        # Adding model 'CustomAction'
        db.create_table('pr_services_customaction', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('blame', self.gf('pr_services.fields.PRForeignKey')(related_name='custom_actions', to=orm['pr_services.Blame'])),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('function_name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=65)),
        ))
        db.send_create_signal('pr_services', ['CustomAction'])

        # Adding model 'Exam'
        db.create_table('pr_services_exam', (
            ('task_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pr_services.Task'], unique=True, primary_key=True)),
            ('passing_score', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('pr_services', ['Exam'])

        # Adding model 'QuestionPool'
        db.create_table('pr_services_questionpool', (
            ('exam', self.gf('pr_services.fields.PRForeignKey')(related_name='question_pools', to=orm['pr_services.Exam'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('randomize_questions', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('next_question_pool', self.gf('pr_services.fields.PRForeignKey')(default=None, to=orm['pr_services.QuestionPool'], null=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=None)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_questionpools', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number_to_answer', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['QuestionPool'])

        # Adding model 'Question'
        db.create_table('pr_services_question', (
            ('rejoinder', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('question_pool', self.gf('pr_services.fields.PRForeignKey')(related_name='questions', to=orm['pr_services.QuestionPool'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('help_text', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_questions', null=True, to=orm['pr_services.User'])),
            ('label', self.gf('django.db.models.fields.TextField')()),
            ('max_length', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True)),
            ('question_type', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('text_regex', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('text_response_label', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('widget', self.gf('django.db.models.fields.CharField')(default=None, max_length=31)),
            ('max_value', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=10)),
            ('min_value', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=10)),
            ('max_answers', self.gf('django.db.models.fields.PositiveIntegerField')(default=1, null=True)),
            ('min_answers', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('text_response', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('min_length', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('required', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=None)),
        ))
        db.send_create_signal('pr_services', ['Question'])

        # Adding model 'Answer'
        db.create_table('pr_services_answer', (
            ('text_response', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('correct', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('end_question_pool', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('end_exam', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('question', self.gf('pr_services.fields.PRForeignKey')(related_name='answers', to=orm['pr_services.Question'])),
            ('next_question_pool', self.gf('pr_services.fields.PRForeignKey')(default=None, to=orm['pr_services.QuestionPool'], null=True)),
            ('value', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=None)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_answers', null=True, to=orm['pr_services.User'])),
            ('label', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('pr_services', ['Answer'])

        # Adding model 'ExamSession'
        db.create_table('pr_services_examsession', (
            ('score', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=5, decimal_places=2)),
            ('assignmentattempt_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pr_services.AssignmentAttempt'], unique=True, primary_key=True)),
            ('passed', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('number_correct', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True)),
        ))
        db.send_create_signal('pr_services', ['ExamSession'])

        # Adding model 'Response'
        db.create_table('pr_services_response', (
            ('password_value', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('correct', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('time_value', self.gf('django.db.models.fields.TimeField')(default=None, null=True)),
            ('bool_value', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('int_value', self.gf('django.db.models.fields.IntegerField')(default=None, null=True)),
            ('question', self.gf('pr_services.fields.PRForeignKey')(related_name='responses', to=orm['pr_services.Question'])),
            ('datetime_value', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
            ('exam_session', self.gf('pr_services.fields.PRForeignKey')(related_name='responses', to=orm['pr_services.ExamSession'])),
            ('decimal_value', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=10)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('date_value', self.gf('django.db.models.fields.DateField')(default=None, null=True)),
            ('char_value', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('valid', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('float_value', self.gf('django.db.models.fields.FloatField')(default=None, null=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_responses', null=True, to=orm['pr_services.User'])),
            ('text_value', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('rating_value', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=None, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['Response'])

        # Adding unique constraint on 'Response', fields ['exam_session', 'question']
        db.create_unique('pr_services_response', ['exam_session_id', 'question_id'])

        # Adding M2M table for field answers on 'Response'
        db.create_table('pr_services_response_answers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('response', models.ForeignKey(orm['pr_services.response'], null=False)),
            ('answer', models.ForeignKey(orm['pr_services.answer'], null=False))
        ))
        db.create_unique('pr_services_response_answers', ['response_id', 'answer_id'])

        # Adding model 'FormPage'
        db.create_table('pr_services_formpage', (
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True)),
            ('number', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('exam', self.gf('pr_services.fields.PRForeignKey')(related_name='form_pages', to=orm['pr_services.Exam'])),
        ))
        db.send_create_signal('pr_services', ['FormPage'])

        # Adding unique constraint on 'FormPage', fields ['exam', 'number']
        db.create_unique('pr_services_formpage', ['exam_id', 'number'])

        # Adding model 'FormWidget'
        db.create_table('pr_services_formwidget', (
            ('y', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('answer', self.gf('pr_services.fields.PRForeignKey')(related_name='form_widgets', null=True, to=orm['pr_services.Answer'])),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('form_page', self.gf('pr_services.fields.PRForeignKey')(related_name='form_widgets', to=orm['pr_services.FormPage'])),
            ('question', self.gf('pr_services.fields.PRForeignKey')(related_name='form_widgets', to=orm['pr_services.Question'])),
            ('height', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_formwidgets', null=True, to=orm['pr_services.User'])),
            ('x', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_services', ['FormWidget'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Note'
        db.delete_table('pr_services_note')

        # Deleting model 'Organization'
        db.delete_table('pr_services_organization')

        # Removing unique constraint on 'Organization', fields ['name', 'parent']
        db.delete_unique('pr_services_organization', ['name', 'parent_id'])

        # Removing M2M table for field notes on 'Organization'
        db.delete_table('pr_services_organization_notes')

        # Deleting model 'OrgRole'
        db.delete_table('pr_services_orgrole')

        # Deleting model 'UserOrgRole'
        db.delete_table('pr_services_userorgrole')

        # Removing unique constraint on 'UserOrgRole', fields ['owner', 'organization', 'role']
        db.delete_unique('pr_services_userorgrole', ['owner_id', 'organization_id', 'role_id'])

        # Deleting model 'OrgEmailDomain'
        db.delete_table('pr_services_orgemaildomain')

        # Removing unique constraint on 'OrgEmailDomain', fields ['email_domain', 'organization', 'role']
        db.delete_unique('pr_services_orgemaildomain', ['email_domain', 'organization_id', 'role_id'])

        # Deleting model 'CredentialType'
        db.delete_table('pr_services_credentialtype')

        # Removing M2M table for field prerequisite_credential_types on 'CredentialType'
        db.delete_table('pr_services_credentialtype_prerequisite_credential_types')

        # Removing M2M table for field notes on 'CredentialType'
        db.delete_table('pr_services_credentialtype_notes')

        # Removing M2M table for field required_achievements on 'CredentialType'
        db.delete_table('pr_services_credentialtype_required_achievements')

        # Deleting model 'Credential'
        db.delete_table('pr_services_credential')

        # Removing M2M table for field notes on 'Credential'
        db.delete_table('pr_services_credential_notes')

        # Deleting model 'Achievement'
        db.delete_table('pr_services_achievement')

        # Removing M2M table for field component_achievements on 'Achievement'
        db.delete_table('pr_services_achievement_component_achievements')

        # Deleting model 'AchievementAward'
        db.delete_table('pr_services_achievementaward')

        # Deleting model 'Task'
        db.delete_table('pr_services_task')

        # Removing M2M table for field achievements on 'Task'
        db.delete_table('pr_services_task_achievements')

        # Removing M2M table for field prerequisite_tasks on 'Task'
        db.delete_table('pr_services_task_prerequisite_tasks')

        # Removing M2M table for field prerequisite_achievements on 'Task'
        db.delete_table('pr_services_task_prerequisite_achievements')

        # Deleting model 'Curriculum'
        db.delete_table('pr_services_curriculum')

        # Removing M2M table for field achievements on 'Curriculum'
        db.delete_table('pr_services_curriculum_achievements')

        # Deleting model 'CurriculumTaskAssociation'
        db.delete_table('pr_services_curriculumtaskassociation')

        # Deleting model 'CurriculumEnrollment'
        db.delete_table('pr_services_curriculumenrollment')

        # Deleting model 'CurriculumEnrollmentUserAssociation'
        db.delete_table('pr_services_curriculumenrollmentuserassociation')

        # Deleting model 'Assignment'
        db.delete_table('pr_services_assignment')

        # Deleting model 'AssignmentAttempt'
        db.delete_table('pr_services_assignmentattempt')

        # Deleting model 'TaskBundle'
        db.delete_table('pr_services_taskbundle')

        # Deleting model 'TaskBundleTaskAssociation'
        db.delete_table('pr_services_taskbundletaskassociation')

        # Deleting model 'ProductLine'
        db.delete_table('pr_services_productline')

        # Removing M2M table for field instructors on 'ProductLine'
        db.delete_table('pr_services_productline_instructors')

        # Removing M2M table for field notes on 'ProductLine'
        db.delete_table('pr_services_productline_notes')

        # Removing M2M table for field instructor_managers on 'ProductLine'
        db.delete_table('pr_services_productline_instructor_managers')

        # Removing M2M table for field managers on 'ProductLine'
        db.delete_table('pr_services_productline_managers')

        # Deleting model 'Region'
        db.delete_table('pr_services_region')

        # Removing M2M table for field notes on 'Region'
        db.delete_table('pr_services_region_notes')

        # Deleting model 'Resource'
        db.delete_table('pr_services_resource')

        # Removing M2M table for field notes on 'Resource'
        db.delete_table('pr_services_resource_notes')

        # Deleting model 'Group'
        db.delete_table('pr_services_group')

        # Removing M2M table for field notes on 'Group'
        db.delete_table('pr_services_group_notes')

        # Removing M2M table for field managers on 'Group'
        db.delete_table('pr_services_group_managers')

        # Deleting model 'Role'
        db.delete_table('pr_services_role')

        # Removing M2M table for field notes on 'Role'
        db.delete_table('pr_services_role_notes')

        # Deleting model 'ACL'
        db.delete_table('pr_services_acl')

        # Deleting model 'ACCheckMethod'
        db.delete_table('pr_services_accheckmethod')

        # Deleting model 'ACMethodCall'
        db.delete_table('pr_services_acmethodcall')

        # Deleting model 'Address'
        db.delete_table('pr_services_address')

        # Deleting model 'Domain'
        db.delete_table('pr_services_domain')

        # Deleting model 'DomainAffiliation'
        db.delete_table('pr_services_domainaffiliation')

        # Removing unique constraint on 'DomainAffiliation', fields ['username', 'domain']
        db.delete_unique('pr_services_domainaffiliation', ['username', 'domain_id'])

        # Deleting model 'User'
        db.delete_table('pr_services_user')

        # Removing M2M table for field notes on 'User'
        db.delete_table('pr_services_user_notes')

        # Removing M2M table for field groups on 'User'
        db.delete_table('pr_services_user_groups')

        # Removing M2M table for field preferred_venues on 'User'
        db.delete_table('pr_services_user_preferred_venues')

        # Deleting model 'Blame'
        db.delete_table('pr_services_blame')

        # Deleting model 'SessionTemplate'
        db.delete_table('pr_services_sessiontemplate')

        # Removing M2M table for field notes on 'SessionTemplate'
        db.delete_table('pr_services_sessiontemplate_notes')

        # Deleting model 'Venue'
        db.delete_table('pr_services_venue')

        # Removing M2M table for field notes on 'Venue'
        db.delete_table('pr_services_venue_notes')

        # Deleting model 'Room'
        db.delete_table('pr_services_room')

        # Removing M2M table for field notes on 'Room'
        db.delete_table('pr_services_room_notes')

        # Deleting model 'Session'
        db.delete_table('pr_services_session')

        # Removing M2M table for field notes on 'Session'
        db.delete_table('pr_services_session_notes')

        # Deleting model 'EventTemplate'
        db.delete_table('pr_services_eventtemplate')

        # Removing M2M table for field notes on 'EventTemplate'
        db.delete_table('pr_services_eventtemplate_notes')

        # Deleting model 'Event'
        db.delete_table('pr_services_event')

        # Removing M2M table for field notes on 'Event'
        db.delete_table('pr_services_event_notes')

        # Deleting model 'SessionUserRole'
        db.delete_table('pr_services_sessionuserrole')

        # Removing M2M table for field notes on 'SessionUserRole'
        db.delete_table('pr_services_sessionuserrole_notes')

        # Deleting model 'ResourceType'
        db.delete_table('pr_services_resourcetype')

        # Removing M2M table for field notes on 'ResourceType'
        db.delete_table('pr_services_resourcetype_notes')

        # Removing M2M table for field resources on 'ResourceType'
        db.delete_table('pr_services_resourcetype_resources')

        # Deleting model 'SessionUserRoleRequirement'
        db.delete_table('pr_services_sessionuserrolerequirement')

        # Removing M2M table for field credential_types on 'SessionUserRoleRequirement'
        db.delete_table('pr_services_sessionuserrolerequirement_credential_types')

        # Removing M2M table for field notes on 'SessionUserRoleRequirement'
        db.delete_table('pr_services_sessionuserrolerequirement_notes')

        # Deleting model 'SessionTemplateUserRoleReq'
        db.delete_table('pr_services_sessiontemplateuserrolereq')

        # Removing M2M table for field notes on 'SessionTemplateUserRoleReq'
        db.delete_table('pr_services_sessiontemplateuserrolereq_notes')

        # Deleting model 'AuthToken'
        db.delete_table('pr_services_authtoken')

        # Deleting model 'SingleUseAuthToken'
        db.delete_table('pr_services_singleuseauthtoken')

        # Deleting model 'AuthTokenVoucher'
        db.delete_table('pr_services_authtokenvoucher')

        # Deleting model 'SessionTemplateResourceTypeReq'
        db.delete_table('pr_services_sessiontemplateresourcetypereq')

        # Removing M2M table for field notes on 'SessionTemplateResourceTypeReq'
        db.delete_table('pr_services_sessiontemplateresourcetypereq_notes')

        # Deleting model 'SessionResourceTypeRequirement'
        db.delete_table('pr_services_sessionresourcetyperequirement')

        # Removing M2M table for field notes on 'SessionResourceTypeRequirement'
        db.delete_table('pr_services_sessionresourcetyperequirement_notes')

        # Removing M2M table for field resources on 'SessionResourceTypeRequirement'
        db.delete_table('pr_services_sessionresourcetyperequirement_resources')

        # Deleting model 'PurchaseOrder'
        db.delete_table('pr_services_purchaseorder')

        # Removing M2M table for field product_discounts on 'PurchaseOrder'
        db.delete_table('pr_services_purchaseorder_product_discounts')

        # Removing M2M table for field notes on 'PurchaseOrder'
        db.delete_table('pr_services_purchaseorder_notes')

        # Deleting model 'TrainingUnitAccount'
        db.delete_table('pr_services_trainingunitaccount')

        # Removing M2M table for field notes on 'TrainingUnitAccount'
        db.delete_table('pr_services_trainingunitaccount_notes')

        # Deleting model 'TrainingUnitTransaction'
        db.delete_table('pr_services_trainingunittransaction')

        # Removing M2M table for field notes on 'TrainingUnitTransaction'
        db.delete_table('pr_services_trainingunittransaction_notes')

        # Deleting model 'TrainingUnitAuthorization'
        db.delete_table('pr_services_trainingunitauthorization')

        # Removing M2M table for field notes on 'TrainingUnitAuthorization'
        db.delete_table('pr_services_trainingunitauthorization_notes')

        # Removing M2M table for field transactions on 'TrainingUnitAuthorization'
        db.delete_table('pr_services_trainingunitauthorization_transactions')

        # Deleting model 'TrainingVoucher'
        db.delete_table('pr_services_trainingvoucher')

        # Removing M2M table for field notes on 'TrainingVoucher'
        db.delete_table('pr_services_trainingvoucher_notes')

        # Deleting model 'Payment'
        db.delete_table('pr_services_payment')

        # Removing M2M table for field notes on 'Payment'
        db.delete_table('pr_services_payment_notes')

        # Deleting model 'Refund'
        db.delete_table('pr_services_refund')

        # Deleting model 'CSVData'
        db.delete_table('pr_services_csvdata')

        # Deleting model 'Product'
        db.delete_table('pr_services_product')

        # Removing M2M table for field notes on 'Product'
        db.delete_table('pr_services_product_notes')

        # Removing M2M table for field custom_actions on 'Product'
        db.delete_table('pr_services_product_custom_actions')

        # Deleting model 'TaskFee'
        db.delete_table('pr_services_taskfee')

        # Deleting model 'ProductClaim'
        db.delete_table('pr_services_productclaim')

        # Removing M2M table for field discounts on 'ProductClaim'
        db.delete_table('pr_services_productclaim_discounts')

        # Deleting model 'ClaimProductOffers'
        db.delete_table('pr_services_claimproductoffers')

        # Removing M2M table for field discounts on 'ClaimProductOffers'
        db.delete_table('pr_services_claimproductoffers_discounts')

        # Deleting model 'ProductTransaction'
        db.delete_table('pr_services_producttransaction')

        # Deleting model 'ProductDiscount'
        db.delete_table('pr_services_productdiscount')

        # Removing M2M table for field notes on 'ProductDiscount'
        db.delete_table('pr_services_productdiscount_notes')

        # Removing M2M table for field product_offers on 'ProductDiscount'
        db.delete_table('pr_services_productdiscount_product_offers')

        # Removing M2M table for field products on 'ProductDiscount'
        db.delete_table('pr_services_productdiscount_products')

        # Deleting model 'ProductOffer'
        db.delete_table('pr_services_productoffer')

        # Removing M2M table for field notes on 'ProductOffer'
        db.delete_table('pr_services_productoffer_notes')

        # Deleting model 'ConditionTestCollection'
        db.delete_table('pr_services_conditiontestcollection')

        # Deleting model 'ConditionTest'
        db.delete_table('pr_services_conditiontest')

        # Removing M2M table for field organizations on 'ConditionTest'
        db.delete_table('pr_services_conditiontest_organizations')

        # Removing M2M table for field session_user_role_requirements on 'ConditionTest'
        db.delete_table('pr_services_conditiontest_session_user_role_requirements')

        # Removing M2M table for field sessions on 'ConditionTest'
        db.delete_table('pr_services_conditiontest_sessions')

        # Removing M2M table for field groups on 'ConditionTest'
        db.delete_table('pr_services_conditiontest_groups')

        # Removing M2M table for field credentials on 'ConditionTest'
        db.delete_table('pr_services_conditiontest_credentials')

        # Removing M2M table for field events on 'ConditionTest'
        db.delete_table('pr_services_conditiontest_events')

        # Deleting model 'Course'
        db.delete_table('pr_services_course')

        # Deleting model 'Sco'
        db.delete_table('pr_services_sco')

        # Deleting model 'ScoSession'
        db.delete_table('pr_services_scosession')

        # Deleting model 'CachedCookie'
        db.delete_table('pr_services_cachedcookie')

        # Deleting model 'CustomAction'
        db.delete_table('pr_services_customaction')

        # Deleting model 'Exam'
        db.delete_table('pr_services_exam')

        # Deleting model 'QuestionPool'
        db.delete_table('pr_services_questionpool')

        # Deleting model 'Question'
        db.delete_table('pr_services_question')

        # Deleting model 'Answer'
        db.delete_table('pr_services_answer')

        # Deleting model 'ExamSession'
        db.delete_table('pr_services_examsession')

        # Deleting model 'Response'
        db.delete_table('pr_services_response')

        # Removing unique constraint on 'Response', fields ['exam_session', 'question']
        db.delete_unique('pr_services_response', ['exam_session_id', 'question_id'])

        # Removing M2M table for field answers on 'Response'
        db.delete_table('pr_services_response_answers')

        # Deleting model 'FormPage'
        db.delete_table('pr_services_formpage')

        # Removing unique constraint on 'FormPage', fields ['exam', 'number']
        db.delete_unique('pr_services_formpage', ['exam_id', 'number'])

        # Deleting model 'FormWidget'
        db.delete_table('pr_services_formwidget')
    
    
    models = {
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pr_services.accheckmethod': {
            'Meta': {'object_name': 'ACCheckMethod'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_accheckmethods'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128', 'unique': 'True'})
        },
        'pr_services.achievement': {
            'Meta': {'object_name': 'Achievement'},
            'component_achievements': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'yielded_achievements'", 'symmetrical': 'False', 'to': "orm['pr_services.Achievement']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'organization': ('pr_services.fields.PRForeignKey', [], {'related_name': "'achievements'", 'null': 'True', 'to': "orm['pr_services.Organization']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_achievements'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'achievements'", 'symmetrical': 'False', 'through': "orm['pr_services.AchievementAward']", 'to': "orm['pr_services.User']"})
        },
        'pr_services.achievementaward': {
            'Meta': {'object_name': 'AchievementAward'},
            'achievement': ('pr_services.fields.PRForeignKey', [], {'related_name': "'achievement_awards'", 'to': "orm['pr_services.Achievement']"}),
            'assignment': ('pr_services.fields.PRForeignKey', [], {'related_name': "'achievement_awards'", 'null': 'True', 'to': "orm['pr_services.Assignment']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('pr_services.fields.PRForeignKey', [], {'related_name': "'achievement_awards'", 'to': "orm['pr_services.User']"})
        },
        'pr_services.acl': {
            'Meta': {'object_name': 'ACL'},
            'ac_check_methods': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'acls'", 'symmetrical': 'False', 'through': "orm['pr_services.ACMethodCall']", 'to': "orm['pr_services.ACCheckMethod']"}),
            'acl': ('django.db.models.fields.TextField', [], {}),
            'arbitrary_perm_list': ('django.db.models.fields.TextField', [], {}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_acls'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'role': ('pr_services.fields.PRForeignKey', [], {'related_name': "'acls'", 'to': "orm['pr_services.Role']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.acmethodcall': {
            'Meta': {'object_name': 'ACMethodCall'},
            'ac_check_method': ('pr_services.fields.PRForeignKey', [], {'related_name': "'ac_method_calls'", 'to': "orm['pr_services.ACCheckMethod']"}),
            'ac_check_parameters': ('django.db.models.fields.TextField', [], {}),
            'acl': ('pr_services.fields.PRForeignKey', [], {'related_name': "'ac_method_calls'", 'to': "orm['pr_services.ACL']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_acmethodcalls'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.address': {
            'Meta': {'object_name': 'Address'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'locality': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '31', 'null': 'True', 'blank': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_addresss'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'postal_code': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '31', 'null': 'True', 'blank': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.answer': {
            'Meta': {'object_name': 'Answer'},
            'correct': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_exam': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'end_question_pool': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'next_question_pool': ('pr_services.fields.PRForeignKey', [], {'default': 'None', 'to': "orm['pr_services.QuestionPool']", 'null': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_answers'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'question': ('pr_services.fields.PRForeignKey', [], {'related_name': "'answers'", 'to': "orm['pr_services.Question']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'text_response': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'})
        },
        'pr_services.assignment': {
            'Meta': {'object_name': 'Assignment'},
            'authority': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'assignments'", 'null': 'True', 'to': "orm['pr_services.Blame']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'curriculum_enrollment': ('pr_services.fields.PRForeignKey', [], {'related_name': "'assignments'", 'null': 'True', 'to': "orm['pr_services.CurriculumEnrollment']"}),
            'date_completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_started': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'due_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'effective_date_assigned': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product_claim': ('pr_services.fields.PRForeignKey', [], {'related_name': "'assignments'", 'null': 'True', 'to': "orm['pr_services.ProductClaim']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sent_confirmation': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'sent_late_notice': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'sent_pre_reminder': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'sent_reminder': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'serial_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'assigned'", 'max_length': '16', 'db_index': 'True'}),
            'task': ('pr_services.fields.PRForeignKey', [], {'related_name': "'assignments'", 'to': "orm['pr_services.Task']"}),
            'user': ('pr_services.fields.PRForeignKey', [], {'related_name': "'assignments'", 'to': "orm['pr_services.User']"})
        },
        'pr_services.assignmentattempt': {
            'Meta': {'object_name': 'AssignmentAttempt'},
            'assignment': ('pr_services.fields.PRForeignKey', [], {'related_name': "'assignment_attempts'", 'to': "orm['pr_services.Assignment']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_started': ('django.db.models.fields.DateTimeField', [], {}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_assignmentattempts'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.authtoken': {
            'Meta': {'object_name': 'AuthToken'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain_affiliation': ('pr_services.fields.PRForeignKey', [], {'related_name': "'auth_tokens'", 'to': "orm['pr_services.DomainAffiliation']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'default': "'0.0.0.0'", 'max_length': '15'}),
            'issue_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'number_of_renewals': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_authtokens'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'renewal_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'unique': 'True', 'db_index': 'True'}),
            'time_of_expiration': ('django.db.models.fields.DateTimeField', [], {})
        },
        'pr_services.authtokenvoucher': {
            'Meta': {'object_name': 'AuthTokenVoucher'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain_affiliation': ('pr_services.fields.PRForeignKey', [], {'related_name': "'auth_token_vouchers'", 'to': "orm['pr_services.DomainAffiliation']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_authtokenvouchers'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'unique': 'True'}),
            'time_of_expiration': ('django.db.models.fields.DateTimeField', [], {})
        },
        'pr_services.blame': {
            'Meta': {'object_name': 'Blame'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_blames'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('pr_services.fields.PRForeignKey', [], {'related_name': "'blamed_user'", 'to': "orm['pr_services.User']"})
        },
        'pr_services.cachedcookie': {
            'Meta': {'object_name': 'CachedCookie'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_cachedcookies'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'pr_services.claimproductoffers': {
            'Meta': {'object_name': 'ClaimProductOffers'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'discounts': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'product_claim'", 'symmetrical': 'False', 'to': "orm['pr_services.ProductDiscount']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_claimproductofferss'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'price_paid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'product_offer': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.ProductOffer']"}),
            'purchase_order': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.PurchaseOrder']"}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'training_units_paid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
        },
        'pr_services.conditiontest': {
            'Meta': {'object_name': 'ConditionTest'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'condition_tests'", 'to': "orm['pr_services.Blame']"}),
            'condition_test_collection': ('pr_services.fields.PRForeignKey', [], {'related_name': "'condition_tests'", 'to': "orm['pr_services.ConditionTestCollection']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'credentials': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'condition_tests'", 'symmetrical': 'False', 'to': "orm['pr_services.Credential']"}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'events': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'condition_tests'", 'symmetrical': 'False', 'to': "orm['pr_services.Event']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'condition_tests'", 'symmetrical': 'False', 'to': "orm['pr_services.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match_all_defined_parameters': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'organizations': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'condition_tests'", 'symmetrical': 'False', 'to': "orm['pr_services.Organization']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'session_user_role_requirements': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'condition_tests'", 'symmetrical': 'False', 'to': "orm['pr_services.SessionUserRoleRequirement']"}),
            'sessions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'condition_tests'", 'symmetrical': 'False', 'to': "orm['pr_services.Session']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        'pr_services.conditiontestcollection': {
            'Meta': {'object_name': 'ConditionTestCollection'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'condition_test_collections'", 'null': 'True', 'to': "orm['pr_services.Blame']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.course': {
            'Meta': {'object_name': 'Course'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_courses'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.credential': {
            'Meta': {'object_name': 'Credential'},
            'authority': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'credential_type': ('pr_services.fields.PRForeignKey', [], {'related_name': "'credentials'", 'to': "orm['pr_services.CredentialType']"}),
            'date_assigned': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_granted': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_started': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'credentials'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_credentials'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'serial_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '8'}),
            'user': ('pr_services.fields.PRForeignKey', [], {'related_name': "'credentials'", 'to': "orm['pr_services.User']"})
        },
        'pr_services.credentialtype': {
            'Meta': {'object_name': 'CredentialType'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'credential_types'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_credentialtypes'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'prerequisite_credential_types': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'requisite_credential_types'", 'symmetrical': 'False', 'to': "orm['pr_services.CredentialType']"}),
            'required_achievements': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'credential_types'", 'symmetrical': 'False', 'to': "orm['pr_services.Achievement']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.csvdata': {
            'Meta': {'object_name': 'CSVData'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_csvdatas'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.User']"})
        },
        'pr_services.curriculum': {
            'Meta': {'object_name': 'Curriculum'},
            'achievements': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'curriculums'", 'symmetrical': 'False', 'to': "orm['pr_services.Achievement']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'organization': ('pr_services.fields.PRForeignKey', [], {'related_name': "'curriculums'", 'null': 'True', 'to': "orm['pr_services.Organization']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'tasks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'curriculums'", 'symmetrical': 'False', 'through': "orm['pr_services.CurriculumTaskAssociation']", 'to': "orm['pr_services.Task']"})
        },
        'pr_services.curriculumenrollment': {
            'Meta': {'object_name': 'CurriculumEnrollment'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'curriculum': ('pr_services.fields.PRForeignKey', [], {'related_name': "'curriculum_enrollments'", 'to': "orm['pr_services.Curriculum']"}),
            'end': ('django.db.models.fields.DateField', [], {}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'curriculum_enrollments'", 'symmetrical': 'False', 'through': "orm['pr_services.CurriculumEnrollmentUserAssociation']", 'to': "orm['pr_services.User']"})
        },
        'pr_services.curriculumenrollmentuserassociation': {
            'Meta': {'object_name': 'CurriculumEnrollmentUserAssociation'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'curriculum_enrollment': ('pr_services.fields.PRForeignKey', [], {'related_name': "'curriculum_enrollment_user_associations'", 'to': "orm['pr_services.CurriculumEnrollment']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('pr_services.fields.PRForeignKey', [], {'related_name': "'curriculum_enrollment_user_associations'", 'to': "orm['pr_services.User']"})
        },
        'pr_services.curriculumtaskassociation': {
            'Meta': {'object_name': 'CurriculumTaskAssociation'},
            'continue_automatically': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'curriculum': ('pr_services.fields.PRForeignKey', [], {'related_name': "'curriculum_task_associations'", 'to': "orm['pr_services.Curriculum']"}),
            'days_before_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'days_to_complete': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentation_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'task': ('pr_services.fields.PRForeignKey', [], {'related_name': "'curriculum_task_associations'", 'to': "orm['pr_services.Task']"}),
            'task_bundle': ('pr_services.fields.PRForeignKey', [], {'related_name': "'curriculum_task_associations'", 'null': 'True', 'to': "orm['pr_services.TaskBundle']"})
        },
        'pr_services.customaction': {
            'Meta': {'object_name': 'CustomAction'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'custom_actions'", 'to': "orm['pr_services.Blame']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'function_name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '65'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.domain': {
            'Meta': {'object_name': 'Domain'},
            'authentication_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'authentication_password_hash': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'password_hash_type': ('django.db.models.fields.CharField', [], {'default': "'SHA-512'", 'max_length': '8'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.domainaffiliation': {
            'Meta': {'unique_together': "(('username', 'domain'),)", 'object_name': 'DomainAffiliation'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'domain': ('pr_services.fields.PRForeignKey', [], {'related_name': "'domain_affiliations'", 'to': "orm['pr_services.Domain']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'may_log_me_in': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'password_hash': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'password_hash_type': ('django.db.models.fields.CharField', [], {'default': "'SHA-512'", 'max_length': '8'}),
            'password_salt': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('pr_services.fields.PRForeignKey', [], {'related_name': "'domain_affiliations'", 'to': "orm['pr_services.User']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '31', 'db_index': 'True'})
        },
        'pr_services.event': {
            'Meta': {'object_name': 'Event'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {}),
            'event_template': ('pr_services.fields.PRForeignKey', [], {'related_name': "'events'", 'null': 'True', 'to': "orm['pr_services.EventTemplate']"}),
            'external_reference': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'facebook_template': ('django.db.models.fields.CharField', [], {'default': "'I just signed up for {{event}}! Click the link to join me.'", 'max_length': '255'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lag_time': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'lead_time': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'events'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'organization': ('pr_services.fields.PRForeignKey', [], {'related_name': "'events'", 'to': "orm['pr_services.Organization']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_events'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'product_line': ('pr_services.fields.PRForeignKey', [], {'related_name': "'events'", 'to': "orm['pr_services.ProductLine']"}),
            'region': ('pr_services.fields.PRForeignKey', [], {'related_name': "'events'", 'null': 'True', 'to': "orm['pr_services.Region']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '127', 'null': 'True'}),
            'twitter_template': ('django.db.models.fields.CharField', [], {'default': "'I just signed up for {{event}}! Join me! {{url}}'", 'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True'}),
            'venue': ('pr_services.fields.PRForeignKey', [], {'related_name': "'events'", 'null': 'True', 'to': "orm['pr_services.Venue']"})
        },
        'pr_services.eventtemplate': {
            'Meta': {'object_name': 'EventTemplate'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'external_reference': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'facebook_template': ('django.db.models.fields.CharField', [], {'default': "'I just signed up for {{event}}! Click the link to join me.'", 'max_length': '255'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lag_time': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'lead_time': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'name_prefix': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'event_templates'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'organization': ('pr_services.fields.PRForeignKey', [], {'related_name': "'event_templates'", 'null': 'True', 'to': "orm['pr_services.Organization']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_eventtemplates'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'product_line': ('pr_services.fields.PRForeignKey', [], {'related_name': "'event_templates'", 'null': 'True', 'to': "orm['pr_services.ProductLine']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '127', 'null': 'True'}),
            'twitter_template': ('django.db.models.fields.CharField', [], {'default': "'I just signed up for {{event}}! Join me! {{url}}'", 'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True'})
        },
        'pr_services.exam': {
            'Meta': {'object_name': 'Exam', '_ormbases': ['pr_services.Task']},
            'passing_score': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pr_services.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        'pr_services.examsession': {
            'Meta': {'object_name': 'ExamSession', '_ormbases': ['pr_services.AssignmentAttempt']},
            'assignmentattempt_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pr_services.AssignmentAttempt']", 'unique': 'True', 'primary_key': 'True'}),
            'number_correct': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True'}),
            'passed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'response_questions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['pr_services.Question']", 'through': "orm['pr_services.Response']", 'symmetrical': 'False'}),
            'score': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '5', 'decimal_places': '2'})
        },
        'pr_services.formpage': {
            'Meta': {'unique_together': "(('exam', 'number'),)", 'object_name': 'FormPage'},
            'exam': ('pr_services.fields.PRForeignKey', [], {'related_name': "'form_pages'", 'to': "orm['pr_services.Exam']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'})
        },
        'pr_services.formwidget': {
            'Meta': {'object_name': 'FormWidget'},
            'answer': ('pr_services.fields.PRForeignKey', [], {'related_name': "'form_widgets'", 'null': 'True', 'to': "orm['pr_services.Answer']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'form_page': ('pr_services.fields.PRForeignKey', [], {'related_name': "'form_widgets'", 'to': "orm['pr_services.FormPage']"}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_formwidgets'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'question': ('pr_services.fields.PRForeignKey', [], {'related_name': "'form_widgets'", 'to': "orm['pr_services.Question']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'x': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'y': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'pr_services.group': {
            'Meta': {'object_name': 'Group'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'managers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'groups_managed'", 'symmetrical': 'False', 'to': "orm['pr_services.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'groups'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_groups'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.note': {
            'Meta': {'object_name': 'Note'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_notes'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'pr_services.organization': {
            'Meta': {'unique_together': "(('name', 'parent'),)", 'object_name': 'Organization'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'address': ('pr_services.fields.PRForeignKey', [], {'related_name': "'organizations'", 'null': 'True', 'to': "orm['pr_services.Address']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'department': ('django.db.models.fields.CharField', [], {'max_length': '127', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_organizations'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'parent': ('pr_services.fields.PRForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['pr_services.Organization']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'primary_contact_cell_phone': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'primary_contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'primary_contact_first_name': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'primary_contact_last_name': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'primary_contact_office_phone': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'primary_contact_other_phone': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'through': "orm['pr_services.UserOrgRole']", 'to': "orm['pr_services.OrgRole']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'})
        },
        'pr_services.orgemaildomain': {
            'Meta': {'unique_together': "(('email_domain', 'organization', 'role'),)", 'object_name': 'OrgEmailDomain'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email_domain': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('pr_services.fields.PRForeignKey', [], {'related_name': "'org_email_domains'", 'to': "orm['pr_services.Organization']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_orgemaildomains'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'role': ('pr_services.fields.PRForeignKey', [], {'related_name': "'org_email_domains'", 'null': 'True', 'to': "orm['pr_services.OrgRole']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.orgrole': {
            'Meta': {'object_name': 'OrgRole'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.payment': {
            'Meta': {'object_name': 'Payment'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'address_label': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'card_number': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'card_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'exp_date': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice_number': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'payments'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_payments'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'purchase_order': ('pr_services.fields.PRForeignKey', [], {'related_name': "'payments'", 'to': "orm['pr_services.PurchaseOrder']"}),
            'result_message': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'sales_tax': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'pr_services.product': {
            'Meta': {'object_name': 'Product'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'products'", 'null': 'True', 'to': "orm['pr_services.Blame']"}),
            'cost': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'custom_actions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'products'", 'symmetrical': 'False', 'to': "orm['pr_services.CustomAction']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'products'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_products'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'price': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '32', 'unique': 'True'}),
            'starting_quantity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'training_units': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'visibility_condition_test_collection': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.ConditionTestCollection']", 'null': 'True'})
        },
        'pr_services.productclaim': {
            'Meta': {'object_name': 'ProductClaim'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_claims'", 'null': 'True', 'to': "orm['pr_services.Blame']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'discounts': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'product_claims'", 'symmetrical': 'False', 'to': "orm['pr_services.ProductDiscount']"}),
            'discounts_searched': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_productclaims'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'price_paid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'product': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_claims'", 'to': "orm['pr_services.Product']"}),
            'purchase_order': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_claims'", 'to': "orm['pr_services.PurchaseOrder']"}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'training_units_paid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
        },
        'pr_services.productdiscount': {
            'Meta': {'object_name': 'ProductDiscount'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_discounts'", 'null': 'True', 'to': "orm['pr_services.Blame']"}),
            'condition_test_collection': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_discounts'", 'null': 'True', 'to': "orm['pr_services.ConditionTestCollection']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'cumulative': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'currency': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '63', 'null': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['pr_services.Note']", 'symmetrical': 'False'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_productdiscounts'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'percentage': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'product_offers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'product_discounts'", 'symmetrical': 'False', 'to': "orm['pr_services.ProductOffer']"}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'product_discounts'", 'symmetrical': 'False', 'to': "orm['pr_services.Product']"}),
            'promo_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'training_units': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
        },
        'pr_services.productline': {
            'Meta': {'object_name': 'ProductLine'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructor_managers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'product_lines_instructor_manager_for'", 'symmetrical': 'False', 'to': "orm['pr_services.User']"}),
            'instructors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'product_lines_instructor_for'", 'symmetrical': 'False', 'to': "orm['pr_services.User']"}),
            'managers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'product_lines_managed'", 'symmetrical': 'False', 'to': "orm['pr_services.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'product_lines'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_productlines'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.productoffer': {
            'Meta': {'object_name': 'ProductOffer'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_offers'", 'null': 'True', 'to': "orm['pr_services.Blame']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['pr_services.Note']", 'symmetrical': 'False'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_productoffers'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'product': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_offers'", 'to': "orm['pr_services.Product']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'seller': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_offers'", 'to': "orm['pr_services.User']"})
        },
        'pr_services.producttransaction': {
            'Meta': {'object_name': 'ProductTransaction'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_transactions'", 'null': 'True', 'to': "orm['pr_services.Blame']"}),
            'change': ('django.db.models.fields.IntegerField', [], {}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_producttransactions'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'product': ('pr_services.fields.PRForeignKey', [], {'related_name': "'product_transactions'", 'to': "orm['pr_services.Product']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.purchaseorder': {
            'Meta': {'object_name': 'PurchaseOrder'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'expiration': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'purchase_orders'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'organization': ('pr_services.fields.PRForeignKey', [], {'related_name': "'purchase_orders'", 'null': 'True', 'to': "orm['pr_services.Organization']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_purchaseorders'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'product_discounts': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'purchase_orders'", 'symmetrical': 'False', 'to': "orm['pr_services.ProductDiscount']"}),
            'product_offers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'purchase_orders'", 'symmetrical': 'False', 'through': "orm['pr_services.ClaimProductOffers']", 'to': "orm['pr_services.ProductOffer']"}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'purchase_orders'", 'symmetrical': 'False', 'through': "orm['pr_services.ProductClaim']", 'to': "orm['pr_services.Product']"}),
            'promo_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'training_units_price': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'training_units_purchased': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.User']", 'null': 'True'})
        },
        'pr_services.question': {
            'Meta': {'object_name': 'Question'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'help_text': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.TextField', [], {}),
            'max_answers': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'max_length': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True'}),
            'max_value': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '10'}),
            'min_answers': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'min_length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'min_value': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_questions'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'question_pool': ('pr_services.fields.PRForeignKey', [], {'related_name': "'questions'", 'to': "orm['pr_services.QuestionPool']"}),
            'question_type': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'rejoinder': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'required': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'text_regex': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'text_response': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'text_response_label': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'widget': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '31'})
        },
        'pr_services.questionpool': {
            'Meta': {'object_name': 'QuestionPool'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'exam': ('pr_services.fields.PRForeignKey', [], {'related_name': "'question_pools'", 'to': "orm['pr_services.Exam']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'next_question_pool': ('pr_services.fields.PRForeignKey', [], {'default': 'None', 'to': "orm['pr_services.QuestionPool']", 'null': 'True'}),
            'number_to_answer': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_questionpools'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'randomize_questions': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'pr_services.refund': {
            'Meta': {'object_name': 'Refund'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_refunds'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'payment': ('pr_services.fields.PRForeignKey', [], {'related_name': "'refunds'", 'to': "orm['pr_services.Payment']"}),
            'result_message': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '63'})
        },
        'pr_services.region': {
            'Meta': {'object_name': 'Region'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'regions'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_regions'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.resource': {
            'Meta': {'object_name': 'Resource'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'resources'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_resources'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.resourcetype': {
            'Meta': {'object_name': 'ResourceType'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'resource_types'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_resourcetypes'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'resources': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'resource_types'", 'symmetrical': 'False', 'to': "orm['pr_services.Resource']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.response': {
            'Meta': {'unique_together': "(('exam_session', 'question'),)", 'object_name': 'Response'},
            'answers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'responses'", 'symmetrical': 'False', 'to': "orm['pr_services.Answer']"}),
            'bool_value': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'char_value': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'correct': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_value': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True'}),
            'datetime_value': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'decimal_value': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '10'}),
            'exam_session': ('pr_services.fields.PRForeignKey', [], {'related_name': "'responses'", 'to': "orm['pr_services.ExamSession']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'float_value': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'int_value': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_responses'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'password_value': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'question': ('pr_services.fields.PRForeignKey', [], {'related_name': "'responses'", 'to': "orm['pr_services.Question']"}),
            'rating_value': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'text_value': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'time_value': ('django.db.models.fields.TimeField', [], {'default': 'None', 'null': 'True'}),
            'valid': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'pr_services.role': {
            'Meta': {'object_name': 'Role'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'roles'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_roles'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.room': {
            'Meta': {'object_name': 'Room'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'capacity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'rooms'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_rooms'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'room_number': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'venue': ('pr_services.fields.PRForeignKey', [], {'related_name': "'rooms'", 'to': "orm['pr_services.Venue']"})
        },
        'pr_services.sco': {
            'Meta': {'object_name': 'Sco', '_ormbases': ['pr_services.Task']},
            'completion_requirement': ('django.db.models.fields.CharField', [], {'default': "'visit_sco'", 'max_length': '64'}),
            'course': ('pr_services.fields.PRForeignKey', [], {'related_name': "'scos'", 'to': "orm['pr_services.Course']"}),
            'data': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pr_services.Task']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'pr_services.scosession': {
            'Meta': {'object_name': 'ScoSession', '_ormbases': ['pr_services.AssignmentAttempt']},
            'assignmentattempt_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pr_services.AssignmentAttempt']", 'unique': 'True', 'primary_key': 'True'}),
            'cmi_core_lesson_location': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'cmi_core_lesson_status': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'cmi_core_score_max': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'cmi_core_score_min': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'shared_object': ('django.db.models.fields.TextField', [], {})
        },
        'pr_services.session': {
            'Meta': {'object_name': 'Session'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'audience': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'confirmed': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'evaluation': ('pr_services.fields.PROneToOneField', [], {'related_name': "'session'", 'unique': 'True', 'null': 'True', 'to': "orm['pr_services.Exam']"}),
            'event': ('pr_services.fields.PRForeignKey', [], {'related_name': "'sessions'", 'to': "orm['pr_services.Event']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'graphic': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modality': ('django.db.models.fields.CharField', [], {'default': "'Generic'", 'max_length': '31'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sessions'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_sessions'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'room': ('pr_services.fields.PRForeignKey', [], {'related_name': "'sessions'", 'null': 'True', 'to': "orm['pr_services.Room']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sent_reminders': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'session_template': ('pr_services.fields.PRForeignKey', [], {'related_name': "'sessions'", 'null': 'True', 'to': "orm['pr_services.SessionTemplate']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '127', 'null': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True'})
        },
        'pr_services.sessionresourcetyperequirement': {
            'Meta': {'object_name': 'SessionResourceTypeRequirement'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'min': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'session_resource_type_requirements'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_sessionresourcetyperequirements'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'resource_type': ('pr_services.fields.PRForeignKey', [], {'related_name': "'sessionresourcetyperequirements'", 'to': "orm['pr_services.ResourceType']"}),
            'resources': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'session_resource_type_requirements'", 'symmetrical': 'False', 'to': "orm['pr_services.Resource']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'session': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Session']"})
        },
        'pr_services.sessiontemplate': {
            'Meta': {'object_name': 'SessionTemplate'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'audience': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'duration': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'event_template': ('pr_services.fields.PRForeignKey', [], {'related_name': "'session_templates'", 'null': 'True', 'to': "orm['pr_services.EventTemplate']"}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lead_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'modality': ('django.db.models.fields.CharField', [], {'default': "'Generic'", 'max_length': '31'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'session_templates'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_sessiontemplates'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'product_line': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.ProductLine']", 'null': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '31', 'unique': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'pr_services.sessiontemplateresourcetypereq': {
            'Meta': {'object_name': 'SessionTemplateResourceTypeReq'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'min': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'session_template_resource_type_requirements'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_sessiontemplateresourcetypereqs'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'resource_type': ('pr_services.fields.PRForeignKey', [], {'related_name': "'sessiontemplateresourcetypereqs'", 'to': "orm['pr_services.ResourceType']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'session_template': ('pr_services.fields.PRForeignKey', [], {'related_name': "'session_template_resource_type_requirements'", 'to': "orm['pr_services.SessionTemplate']"})
        },
        'pr_services.sessiontemplateuserrolereq': {
            'Meta': {'object_name': 'SessionTemplateUserRoleReq'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'min': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'session_template_user_role_requirements'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_sessiontemplateuserrolereqs'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'session_template': ('pr_services.fields.PRForeignKey', [], {'related_name': "'session_template_user_role_requirements'", 'to': "orm['pr_services.SessionTemplate']"}),
            'session_user_role': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.SessionUserRole']"})
        },
        'pr_services.sessionuserrole': {
            'Meta': {'object_name': 'SessionUserRole'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'session_user_roles'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_sessionuserroles'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.sessionuserrolerequirement': {
            'Meta': {'object_name': 'SessionUserRoleRequirement', '_ormbases': ['pr_services.Task']},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'credential_types': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'session_user_role_requirements'", 'symmetrical': 'False', 'to': "orm['pr_services.CredentialType']"}),
            'enrollment_status_test': ('pr_services.fields.PRForeignKey', [], {'related_name': "'session_user_role_requirements'", 'null': 'True', 'to': "orm['pr_services.ConditionTestCollection']"}),
            'ignore_room_capacity': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'session_user_role_requirements'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'session': ('pr_services.fields.PRForeignKey', [], {'related_name': "'session_user_role_requirements'", 'to': "orm['pr_services.Session']"}),
            'session_user_role': ('pr_services.fields.PRForeignKey', [], {'related_name': "'session_user_role_requirements'", 'to': "orm['pr_services.SessionUserRole']"}),
            'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pr_services.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        'pr_services.singleuseauthtoken': {
            'Meta': {'object_name': 'SingleUseAuthToken', '_ormbases': ['pr_services.AuthToken']},
            'authtoken_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pr_services.AuthToken']", 'unique': 'True', 'primary_key': 'True'}),
            'used': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'pr_services.task': {
            'Meta': {'object_name': 'Task'},
            'achievements': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'tasks'", 'symmetrical': 'False', 'to': "orm['pr_services.Achievement']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_tasks'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'prerequisite_achievements': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'yielded_tasks'", 'symmetrical': 'False', 'to': "orm['pr_services.Achievement']"}),
            'prerequisite_tasks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'yielded_tasks'", 'symmetrical': 'False', 'to': "orm['pr_services.Task']"}),
            'prevent_duplicate_assignments': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'public': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'tasks'", 'symmetrical': 'False', 'through': "orm['pr_services.Assignment']", 'to': "orm['pr_services.User']"}),
            'version_comment': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'version_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'version_label': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        'pr_services.taskbundle': {
            'Meta': {'object_name': 'TaskBundle'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'organization': ('pr_services.fields.PRForeignKey', [], {'related_name': "'task_bundles'", 'null': 'True', 'to': "orm['pr_services.Organization']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'tasks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'task_bundles'", 'symmetrical': 'False', 'through': "orm['pr_services.TaskBundleTaskAssociation']", 'to': "orm['pr_services.Task']"})
        },
        'pr_services.taskbundletaskassociation': {
            'Meta': {'object_name': 'TaskBundleTaskAssociation'},
            'continue_automatically': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'presentation_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'task': ('pr_services.fields.PRForeignKey', [], {'related_name': "'task_bundle_task_associations'", 'to': "orm['pr_services.Task']"}),
            'task_bundle': ('pr_services.fields.PRForeignKey', [], {'related_name': "'task_bundle_task_associations'", 'to': "orm['pr_services.TaskBundle']"})
        },
        'pr_services.taskfee': {
            'Meta': {'object_name': 'TaskFee', '_ormbases': ['pr_services.Product']},
            'product_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pr_services.Product']", 'unique': 'True', 'primary_key': 'True'}),
            'task': ('pr_services.fields.PRForeignKey', [], {'related_name': "'task_fees'", 'to': "orm['pr_services.Task']"})
        },
        'pr_services.trainingunitaccount': {
            'Meta': {'object_name': 'TrainingUnitAccount'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['pr_services.Note']", 'symmetrical': 'False'}),
            'organization': ('pr_services.fields.PRForeignKey', [], {'related_name': "'trainingunitaccounts'", 'null': 'True', 'to': "orm['pr_services.Organization']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_trainingunitaccounts'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'starting_value': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.User']", 'null': 'True'})
        },
        'pr_services.trainingunitauthorization': {
            'Meta': {'object_name': 'TrainingUnitAuthorization'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_value': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['pr_services.Note']", 'symmetrical': 'False'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_trainingunitauthorizations'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'training_unit_account': ('pr_services.fields.PRForeignKey', [], {'related_name': "'training_unit_authorizations'", 'to': "orm['pr_services.TrainingUnitAccount']"}),
            'transactions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'training_unit_authorizations'", 'symmetrical': 'False', 'to': "orm['pr_services.TrainingUnitTransaction']"}),
            'user': ('pr_services.fields.PRForeignKey', [], {'related_name': "'training_unit_authorizations'", 'to': "orm['pr_services.User']"})
        },
        'pr_services.trainingunittransaction': {
            'Meta': {'object_name': 'TrainingUnitTransaction'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['pr_services.Note']", 'symmetrical': 'False'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_trainingunittransactions'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'purchase_order': ('pr_services.fields.PRForeignKey', [], {'related_name': "'training_unit_transactions'", 'to': "orm['pr_services.PurchaseOrder']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'training_unit_account': ('pr_services.fields.PRForeignKey', [], {'related_name': "'training_unit_transactions'", 'to': "orm['pr_services.TrainingUnitAccount']"}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        'pr_services.trainingvoucher': {
            'Meta': {'object_name': 'TrainingVoucher'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'training_vouchers'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_trainingvouchers'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'purchase_order': ('pr_services.fields.PRForeignKey', [], {'related_name': "'training_vouchers'", 'null': 'True', 'to': "orm['pr_services.PurchaseOrder']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'session_user_role_requirement': ('pr_services.fields.PRForeignKey', [], {'related_name': "'training_vouchers'", 'to': "orm['pr_services.SessionUserRoleRequirement']"})
        },
        'pr_services.user': {
            'Meta': {'object_name': 'User'},
            'alleged_organization': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'billing_address': ('pr_services.fields.PRForeignKey', [], {'related_name': "'users_billing'", 'null': 'True', 'to': "orm['pr_services.Address']"}),
            'biography': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'created_users'", 'null': 'True', 'to': "orm['pr_services.Blame']"}),
            'color_code': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'confirmation_code': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domains': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users'", 'symmetrical': 'False', 'through': "orm['pr_services.DomainAffiliation']", 'to': "orm['pr_services.Domain']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'email2': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            'enable_paypal': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users'", 'symmetrical': 'False', 'to': "orm['pr_services.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_staff': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '31'}),
            'name_suffix': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'organizations': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users'", 'symmetrical': 'False', 'through': "orm['pr_services.UserOrgRole']", 'to': "orm['pr_services.Organization']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_users'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'paypal_address': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'phone2': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'phone3': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'preferred_venues': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users_who_prefer_this_venue'", 'symmetrical': 'False', 'null': 'True', 'to': "orm['pr_services.Venue']"}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users'", 'symmetrical': 'False', 'through': "orm['pr_services.UserOrgRole']", 'to': "orm['pr_services.OrgRole']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'shipping_address': ('pr_services.fields.PRForeignKey', [], {'related_name': "'users_shipping'", 'null': 'True', 'to': "orm['pr_services.Address']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'suppress_emails': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'})
        },
        'pr_services.userorgrole': {
            'Meta': {'unique_together': "(('owner', 'organization', 'role'),)", 'object_name': 'UserOrgRole'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('pr_services.fields.PRForeignKey', [], {'related_name': "'user_org_roles'", 'to': "orm['pr_services.Organization']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_userorgroles'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'parent': ('pr_services.fields.PRForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['pr_services.UserOrgRole']"}),
            'role': ('pr_services.fields.PRForeignKey', [], {'related_name': "'user_org_roles'", 'to': "orm['pr_services.OrgRole']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'pr_services.venue': {
            'Meta': {'object_name': 'Venue'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'address': ('pr_services.fields.PRForeignKey', [], {'related_name': "'venues'", 'null': 'True', 'to': "orm['pr_services.Address']"}),
            'blame': ('pr_services.fields.PRForeignKey', [], {'to': "orm['pr_services.Blame']", 'null': 'True'}),
            'contact': ('django.db.models.fields.CharField', [], {'max_length': '63', 'null': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'hours_of_operation': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'venue'", 'symmetrical': 'False', 'to': "orm['pr_services.Note']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_venues'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'region': ('pr_services.fields.PRForeignKey', [], {'related_name': "'venues'", 'to': "orm['pr_services.Region']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['pr_services']
