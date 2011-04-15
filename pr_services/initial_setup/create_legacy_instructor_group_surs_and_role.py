import facade
from decorators import authz

@authz
def setup(machine):
    sur, created = facade.models.SessionUserRole.objects.get_or_create(
        name='Instructor')
    student_sur, created = facade.models.SessionUserRole.objects.get_or_create(
        name='Student')
    group, created = facade.models.Group.objects.get_or_create(
        name='Instructors')

    methods = [
        {'name' : 'actor_member_of_group', 'params' : {'group_id' : group.id}},
        {'name' : 'actor_actee_enrolled_in_same_session', 'params' : {
            'actor_sur_id' : sur.id, 'actee_sur_id' : student_sur.id}},
    ]
    crud = {
        'User' : {
            'c' : True,
            'r' : ['credentials',
                   'session_user_role_requirements', 'product_lines_managed',
                   'product_lines_instructor_manager_for', 'product_lines_instructor_for',
                   'groups', 'photo_url', 'url', 'username', 'domains',
                   'title', 'first_name', 'middle_name', 'last_name', 'name_suffix',
                   'full_name',
                   'phone', 'phone2', 'phone3', 'email', 'email2',
                   'status', 'color_code', 'biography',
                   'shipping_address', 'billing_address',],
            'u' : ['credentials',
                   'groups', 'photo_url',
                   'url',
                   'title', 'first_name', 'middle_name', 'last_name', 'name_suffix',
                   'phone', 'phone2', 'phone3', 'email', 'email2',
                   'status', 'color_code', 'biography', 'shipping_address',
                   'billing_address',],
            'd' : True,
        },
    }
    machine.add_acl_to_role('Instructor', methods, crud)
