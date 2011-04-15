# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'paypal_ec_token'
        db.create_table('ecommerce_paypal_ec_token', (
            ('amount', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('ecommerce', ['paypal_ec_token'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'paypal_ec_token'
        db.delete_table('ecommerce_paypal_ec_token')
    
    
    models = {
        'ecommerce.paypal_ec_token': {
            'Meta': {'object_name': 'paypal_ec_token'},
            'amount': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }
    
    complete_apps = ['ecommerce']
