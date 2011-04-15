"""
Organization manager class
"""

import facade
from pr_services import storage
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
from pr_services.utils import upload, Utils

class OrganizationManager(ObjectManager):
    """
    Manage companies in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update({
            'address' : 'get_address',
            'ancestors' : 'get_general',
            'children' : 'get_many_to_one',
            'department' : 'get_general',
            'descendants' : 'get_general',
            'description' : 'get_general',
            'email' : 'get_general',
            'fax' : 'get_general',
            'name' : 'get_general',
            'org_email_domains' : 'get_many_to_one',
            'parent' : 'get_foreign_key',
            'phone' : 'get_general',
            'photo_url' : 'get_photo_url',
            'primary_contact_first_name' : 'get_general',
            'primary_contact_last_name' : 'get_general',
            'primary_contact_office_phone' : 'get_general',
            'primary_contact_cell_phone' : 'get_general',
            'primary_contact_other_phone' : 'get_general',
            'primary_contact_email' : 'get_general',
            'purchase_orders' : 'get_many_to_one',
            'roles' : 'get_many_to_many',
            'training_unit_accounts' : 'get_many_to_one',
            'url' : 'get_general',
            'user_org_roles' : 'get_many_to_one',
            'users' : 'get_many_to_many',
        })
        self.setters.update({
            'address' : 'set_address',
            'department' : 'set_general',
            'description' : 'set_general',
            'email' : 'set_general',
            'fax' : 'set_general',
            'name' : 'set_general',
            'parent' : 'set_foreign_key',
            'phone' : 'set_general',
            'photo_url' : 'set_forbidden', # placeholder
            'primary_contact_first_name' : 'set_general',
            'primary_contact_last_name' : 'set_general',
            'primary_contact_office_phone' : 'set_general',
            'primary_contact_cell_phone' : 'set_general',
            'primary_contact_other_phone' : 'set_general',
            'primary_contact_email' : 'set_general',
            'roles' : 'set_many',
            'url' : 'set_general',
            'users' : 'set_many',
        })
        self.my_django_model = facade.models.Organization
        self.photo_storage_engine = storage.OrganizationPhotoStorage()

    @service_method
    def create(self, auth_token, name, optional_attributes = None):
        """
        Create a new Organization
        
        @param name                 name of the Organization
        @param optional_attributes  Optional dict with values indexed as 'department', 'address', 'fax',
                                    'phone', 'description', 'org_email_domains', 'primary_contact_first_name', 'primary_contact_last_name',
                                    'primary_contact_office_phone', 'primary_contact_cell_phone', 'primary_contact_other_phone',
                                    'primary_contact_email'
        @return                     a reference to the newly created Organization
        """

        o = self.my_django_model(name=name)
        if isinstance(optional_attributes, dict) and 'parent' in optional_attributes:
            o.parent = self._find_by_id(optional_attributes['parent'])
            del optional_attributes['parent']
        o.save()
        if optional_attributes is not None:
            facade.subsystems.Setter(auth_token, self, o, optional_attributes)
            o.save()
        self.authorizer.check_create_permissions(auth_token, o)
        return o

    def upload_organization_photo(self, request):
        """Handle Image file uploads for Organization photos

        :param request:   HttpRequest object from django

        """
        return upload._upload_photo(request, self, 'organization_id', storage.OrganizationPhotoStorage())

    @service_method
    def admin_org_view(self, auth_token):
        orgs = self.get_filtered(auth_token, {}, ['name', 'parent', 'user_org_roles', 'org_email_domains'])
        
        ret = Utils.merge_queries(orgs, facade.managers.OrgEmailDomainManager(), auth_token, ['email_domain', 'effective_role', 'effective_role_name'], 'org_email_domains')
        
        return Utils.merge_queries(ret, facade.managers.UserOrgRoleManager(), auth_token, ['role_name', 'role', 'owner'], 'user_org_roles')

    @service_method
    def admin_org_user_view(self, auth_token, org):
        ret = facade.managers.UserOrgRoleManager().get_filtered(auth_token, {'exact' : {'organization' : org}}, ['role', 'owner'])

        ret = Utils.merge_queries(ret, facade.managers.UserManager(), auth_token, ['first_name', 'last_name', 'email'], 'owner')

        return Utils.merge_queries(ret, facade.managers.OrgRoleManager(), auth_token, ['name'], 'role')

# vim:tabstop=4 shiftwidth=4 expandtab
