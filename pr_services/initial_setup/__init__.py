"""
initial setup for the power reg 2 application
"""

import cPickle
import facade

# the default fields that everyone should be able to read for any
# model they have access to
default_read_fields = ['id', 'content_type', 'create_timestamp',
    'save_timestamp']

class InitialSetupMachine(object):
    def __init__(self):
        # what initializer methods to call, by category name
        # category base is always called, legacy is the default
        self.initializers = {
            'base' : [
              'import_ac_check_methods',
              'create_default_domains',
              'create_admin_user_group_and_role',
              'create_object_owner_role',
              'create_authenticated_user_role',
              'create_guest_role',
              'import_message_templates',
              'import_regions',
              'import_venues',
            ],
            'legacy' : [
              'create_legacy_user_role',
              'create_legacy_student_group_and_role',
              'create_legacy_instructor_group_surs_and_role',
              'create_legacy_group_manager_role',
              'create_legacy_product_line_manager_role',
              'create_legacy_instructor_manager_role',
              'create_legacy_paid_purchase_order_owner_role',
              'create_legacy_unpaid_purchase_order_owner_role',
              # we have tests that depend on this fixture, but also on legacy
              # roles, so let's import this here too
              'import_precor_org_roles',
            ],
            'precor' : [
              'import_precor_org_roles',
              'import_precor_orgs',
              'create_category_manager_group_and_role',
              'create_video_uploader_role',
              'create_video_watcher_role',
              'create_precor_default_group',
            ],
        }

        self.user_manager = facade.managers.UserManager()
        self.import_manager = facade.managers.ImportManager()

    def add_default_read_fields_to_acl(self, acl):
        """
        Add the default read fields to the list of readable attributes for every
        model listed in an ACL.
        
        :param acl: dictionary representation of the ACL
        :type acl: dict
        """
        
        for model_name in acl:
            if acl[model_name].has_key('r'):
                for field in default_read_fields:
                    if field not in acl[model_name]['r']:
                        acl[model_name]['r'].append(field)

    def add_acl_to_role(self, name, methods, crud, arbitrary_perms=None):
        """
        Create model objects to represent an ACL for an authorizer role.
        
        :param name: Name of the role to work with (created if necessary).
        :type name: str
        :param methods: A list of dictionaries, each containing the name of an ACCheckMethod and a dict of params to pass to it.
        :type methods: list
        :param crud: A dictionary that maps model names to CRUD permissions.
        :type crud: dict
        :param arbitrary_perms: A list of strings representing arbitrary permissions.
        :type arbitrary_perms: list
        """
        role, created = facade.models.Role.objects.get_or_create(name=name)
        self.add_default_read_fields_to_acl(crud)
        crud = cPickle.dumps(crud)
        if arbitrary_perms is not None:
            arbitrary_perms = cPickle.dumps(arbitrary_perms)
        else:
            arbitrary_perms = ''
        acl = facade.models.ACL.objects.create(role=role, acl=crud,
            arbitrary_perm_list=arbitrary_perms)
        for m in methods:
            method = facade.models.ACCheckMethod.objects.get(name=m['name'])
            facade.models.ACMethodCall.objects.create(acl=acl,
                ac_check_method=method,
                ac_check_parameters=cPickle.dumps(m['params']))

    def call_setup_method(self, name, authz_only=False):
        """A helper for calling the setup methods we define in this package's modules."""
        exec 'from . import %s as method' % name
        authz_method = getattr(method.setup, 'authz', False)
        if not authz_only or authz_method:
            method.setup(self)

    def initial_setup(self, *args, **options):
        """Set up the initial state of the database."""
        self.options = options
        if not len(args):
            args = ['base', 'legacy']
        else:
            args = list(args)
            if 'base' in args:
                args.remove('base')
            args.insert(0, 'base')
        if options.get('templates_only'):
            self.call_setup_method('clear_message_templates')
            self.call_setup_method('import_message_templates')
            return
        if not options.has_key('authz_only'):
            options['authz_only'] = False
        elif options['authz_only']:
            self.call_setup_method('clear_authz_data')
        for category in args:
            for method in self.initializers[category]:
                self.call_setup_method(method, options['authz_only'])
        # remove the admin_token we may have created during setup
        if self.options.has_key('admin_token'):
            self.user_manager.logout(self.options['admin_token'])
        # we need to reload the ACLs because we just modified them
        facade.subsystems.Authorizer()._load_acls()

# vim:tabstop=4 shiftwidth=4 expandtab
