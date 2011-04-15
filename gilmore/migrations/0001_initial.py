# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'LineItem'
        db.create_table('gilmore_lineitem', (
            ('sku', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('order', self.gf('pr_services.fields.PRForeignKey')(related_name='line_items', to=orm['gilmore.Order'])),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_lineitems', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('gilmore', ['LineItem'])

        # Adding model 'Order'
        db.create_table('gilmore_order', (
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
            ('locality', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('confirmation_code', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=31)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=31, null=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_orders', null=True, to=orm['pr_services.User'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('shipment_method', self.gf('pr_services.fields.PRForeignKey')(related_name='orders', to=orm['gilmore.ShipmentMethod'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sent', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('gilmore', ['Order'])

        # Adding model 'ShipmentMethod'
        db.create_table('gilmore_shipmentmethod', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=16, unique=True)),
            ('save_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=63, unique=True)),
            ('active', self.gf('pr_services.fields.PRBooleanField')(default=True, blank=True)),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('pr_services.fields.PRForeignKey')(related_name='owned_shipmentmethods', null=True, to=orm['pr_services.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('final_type', self.gf('pr_services.fields.PRForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('gilmore', ['ShipmentMethod'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'LineItem'
        db.delete_table('gilmore_lineitem')

        # Deleting model 'Order'
        db.delete_table('gilmore_order')

        # Deleting model 'ShipmentMethod'
        db.delete_table('gilmore_shipmentmethod')
    
    
    models = {
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'gilmore.lineitem': {
            'Meta': {'object_name': 'LineItem'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('pr_services.fields.PRForeignKey', [], {'related_name': "'line_items'", 'to': "orm['gilmore.Order']"}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_lineitems'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'quantity': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '31'})
        },
        'gilmore.order': {
            'Meta': {'object_name': 'Order'},
            'confirmation_code': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'locality': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_orders'", 'null': 'True', 'to': "orm['pr_services.User']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '31', 'null': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'save_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'shipment_method': ('pr_services.fields.PRForeignKey', [], {'related_name': "'orders'", 'to': "orm['gilmore.ShipmentMethod']"})
        },
        'gilmore.shipmentmethod': {
            'Meta': {'object_name': 'ShipmentMethod'},
            'active': ('pr_services.fields.PRBooleanField', [], {'default': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '16', 'unique': 'True'}),
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'final_type': ('pr_services.fields.PRForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '63', 'unique': 'True'}),
            'owner': ('pr_services.fields.PRForeignKey', [], {'related_name': "'owned_shipmentmethods'", 'null': 'True', 'to': "orm['pr_services.User']"}),
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
    
    complete_apps = ['gilmore']
