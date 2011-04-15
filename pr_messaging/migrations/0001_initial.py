# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'MessageFormat'
        db.create_table('pr_messaging_messageformat', (
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=32, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('pr_messaging', ['MessageFormat'])

        # Adding model 'MessageType'
        db.create_table('pr_messaging_messagetype', (
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('multiple_recipients', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('pr_messaging', ['MessageType'])

        # Adding model 'MessageTemplate'
        db.create_table('pr_messaging_messagetemplate', (
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('message_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='message_templates', to=orm['pr_messaging.MessageType'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message_format', self.gf('django.db.models.fields.related.ForeignKey')(related_name='message_templates', to=orm['pr_messaging.MessageFormat'])),
        ))
        db.send_create_signal('pr_messaging', ['MessageTemplate'])

        # Adding unique constraint on 'MessageTemplate', fields ['message_type', 'message_format']
        db.create_unique('pr_messaging_messagetemplate', ['message_type_id', 'message_format_id'])

        # Adding model 'SentMessage'
        db.create_table('pr_messaging_sentmessage', (
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message_template', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sent_messages', to=orm['pr_messaging.MessageTemplate'])),
        ))
        db.send_create_signal('pr_messaging', ['SentMessage'])

        # Adding model 'SentMessageParticipant'
        db.create_table('pr_messaging_sentmessageparticipant', (
            ('participant_contact', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('sent_message', self.gf('django.db.models.fields.related.ForeignKey')(related_name='participants', to=orm['pr_messaging.SentMessage'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['contenttypes.ContentType'], null=True)),
            ('participant_id', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('pr_messaging', ['SentMessageParticipant'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'MessageFormat'
        db.delete_table('pr_messaging_messageformat')

        # Deleting model 'MessageType'
        db.delete_table('pr_messaging_messagetype')

        # Deleting model 'MessageTemplate'
        db.delete_table('pr_messaging_messagetemplate')

        # Removing unique constraint on 'MessageTemplate', fields ['message_type', 'message_format']
        db.delete_unique('pr_messaging_messagetemplate', ['message_type_id', 'message_format_id'])

        # Deleting model 'SentMessage'
        db.delete_table('pr_messaging_sentmessage')

        # Deleting model 'SentMessageParticipant'
        db.delete_table('pr_messaging_sentmessageparticipant')
    
    
    models = {
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pr_messaging.messageformat': {
            'Meta': {'object_name': 'MessageFormat'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'})
        },
        'pr_messaging.messagetemplate': {
            'Meta': {'unique_together': "(('message_type', 'message_format'),)", 'object_name': 'MessageTemplate'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_format': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'message_templates'", 'to': "orm['pr_messaging.MessageFormat']"}),
            'message_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'message_templates'", 'to': "orm['pr_messaging.MessageType']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'pr_messaging.messagetype': {
            'Meta': {'object_name': 'MessageType'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'multiple_recipients': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'pr_messaging.sentmessage': {
            'Meta': {'object_name': 'SentMessage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_messages'", 'to': "orm['pr_messaging.MessageTemplate']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'pr_messaging.sentmessageparticipant': {
            'Meta': {'object_name': 'SentMessageParticipant'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participant_contact': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'participant_id': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'sent_message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'participants'", 'to': "orm['pr_messaging.SentMessage']"})
        }
    }
    
    complete_apps = ['pr_messaging']
