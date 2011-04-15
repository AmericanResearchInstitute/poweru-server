from decorators import authz

@authz
def setup(machine):
    methods = [
        {'name' : 'actor_is_instructor_manager_of_actee', 'params' : {}},
    ]
    crud = {
        'User' : {
            'c' : True,
            'r' : ['credentials',
                   'session_user_role_requirements', 'product_lines_managed',
                   'product_lines_instructor_manager_for', 'product_lines_instructor_for',
                   'groups', 'photo_url', 'url', 'username',
                   'title', 'first_name', 'middle_name', 'last_name', 'name_suffix',
                   'full_name',
                   'phone', 'phone2', 'phone3', 'email', 'email2',
                   'status', 'color_code', 'biography',
                   'shipping_address', 'billing_address',
                   'default_username_and_domain',],
            'u' : ['credentials',
                   'groups', 'photo_url', 'url',
                   'title', 'first_name', 'middle_name', 'last_name', 'name_suffix',
                   'phone', 'phone2', 'phone3', 'email', 'email2', 'status',
                   'color_code', 'biography',
                   'shipping_address', 'billing_address'],
            'd' : True,
        },
    }
    machine.add_acl_to_role('Instructor Manager', methods, crud)
