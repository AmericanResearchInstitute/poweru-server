# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Video'
        db.create_table('vod_aws_video', (
            ('task_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pr_services.Task'], unique=True, primary_key=True)),
            ('encoding_job_mediaid', self.gf('django.db.models.fields.CharField')(max_length=38)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('src_file_size', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('photo', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('live', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('deleted', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('length', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('is_ready', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('aspect_ratio', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('src_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('vod_aws', ['Video'])

        # Adding model 'Category'
        db.create_table('vod_aws_category', (
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('locked', self.gf('pr_services.fields.PRBooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('vod_aws', ['Category'])

        # Adding M2M table for field authorized_groups on 'Category'
        db.create_table('vod_aws_category_authorized_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('category', models.ForeignKey(orm['vod_aws.category'], null=False)),
            ('group', models.ForeignKey(orm['pr_services.group'], null=False))
        ))
        db.create_unique('vod_aws_category_authorized_groups', ['category_id', 'group_id'])

        # Adding M2M table for field managers on 'Category'
        db.create_table('vod_aws_category_managers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('category', models.ForeignKey(orm['vod_aws.category'], null=False)),
            ('user', models.ForeignKey(orm['pr_services.user'], null=False))
        ))
        db.create_unique('vod_aws_category_managers', ['category_id', 'user_id'])

        # Adding model 'VideoCategory'
        db.create_table('vod_aws_videocategory', (
            ('category', self.gf('pr_services.fields.PRForeignKey')(related_name='video_relationships', to=orm['vod_aws.Category'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='pending', max_length=15)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('video', self.gf('pr_services.fields.PRForeignKey')(related_name='category_relationships', to=orm['vod_aws.Video'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('vod_aws', ['VideoCategory'])

        # Adding unique constraint on 'VideoCategory', fields ['video', 'category']
        db.create_unique('vod_aws_videocategory', ['video_id', 'category_id'])

        # Adding model 'EncodedVideo'
        db.create_table('vod_aws_encodedvideo', (
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('video', self.gf('pr_services.fields.PRForeignKey')(related_name='encoded_videos', to=orm['vod_aws.Video'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('audio_codec', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('video_codec', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_encodedvideos', null=True, to=orm['pr_services.User'])),
            ('output', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('bitrate', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('size', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal('vod_aws', ['EncodedVideo'])

        # Adding model 'VideoSession'
        db.create_table('vod_aws_videosession', (
            ('assignmentattempt_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pr_services.AssignmentAttempt'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('vod_aws', ['VideoSession'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Video'
        db.delete_table('vod_aws_video')

        # Deleting model 'Category'
        db.delete_table('vod_aws_category')

        # Removing M2M table for field authorized_groups on 'Category'
        db.delete_table('vod_aws_category_authorized_groups')

        # Removing M2M table for field managers on 'Category'
        db.delete_table('vod_aws_category_managers')

        # Deleting model 'VideoCategory'
        db.delete_table('vod_aws_videocategory')

        # Removing unique constraint on 'VideoCategory', fields ['video', 'category']
        db.delete_unique('vod_aws_videocategory', ['video_id', 'category_id'])

        # Deleting model 'EncodedVideo'
        db.delete_table('vod_aws_encodedvideo')

        # Deleting model 'VideoSession'
        db.delete_table('vod_aws_videosession')
    
    
    models = {
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        'pr_services.conditiontestcollection': {
            'Meta': {'object_name': 'ConditionTestCollection'},
            'blame': ('pr_services.fields.PRForeignKey', [], {'related_name': "'condition_test_collections'", 'null': 'True', 'to': "orm['pr_services.Blame']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
        'pr_services.orgrole': {
            'Meta': {'object_name': 'OrgRole'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
        },
        'vod_aws.category': {
            'Meta': {'object_name': 'Category'},
            'authorized_groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'categories'", 'symmetrical': 'False', 'to': "orm['pr_services.Group']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'managers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'categories'", 'symmetrical': 'False', 'to': "orm['pr_services.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'vod_aws.encodedvideo': {
            'Meta': {'object_name': 'EncodedVideo'},
            'audio_codec': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'bitrate': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'output': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_encodedvideos'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'video': ('pr_services.fields.PRForeignKey', [], {'related_name': "'encoded_videos'", 'to': "orm['vod_aws.Video']"}),
            'video_codec': ('django.db.models.fields.CharField', [], {'max_length': '31'})
        },
        'vod_aws.video': {
            'Meta': {'object_name': 'Video', '_ormbases': ['pr_services.Task']},
            'aspect_ratio': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'videos'", 'symmetrical': 'False', 'through': "orm['vod_aws.VideoCategory']", 'to': "orm['vod_aws.Category']"}),
            'deleted': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'encoding_job_mediaid': ('django.db.models.fields.CharField', [], {'max_length': '38'}),
            'is_ready': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'length': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'live': ('pr_services.fields.PRBooleanField', [], {'default': 'False', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'src_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'src_file_size': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pr_services.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        'vod_aws.videocategory': {
            'Meta': {'unique_together': "(('video', 'category'),)", 'object_name': 'VideoCategory'},
            'category': ('pr_services.fields.PRForeignKey', [], {'related_name': "'video_relationships'", 'to': "orm['vod_aws.Category']"}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '15'}),
            'video': ('pr_services.fields.PRForeignKey', [], {'related_name': "'category_relationships'", 'to': "orm['vod_aws.Video']"})
        },
        'vod_aws.videosession': {
            'Meta': {'object_name': 'VideoSession', '_ormbases': ['pr_services.AssignmentAttempt']},
            'assignmentattempt_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pr_services.AssignmentAttempt']", 'unique': 'True', 'primary_key': 'True'})
        }
    }
    
    complete_apps = ['vod_aws']
