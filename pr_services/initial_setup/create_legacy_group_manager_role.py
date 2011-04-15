from decorators import authz

@authz
def setup(machine):
    methods = [
        {'name' : 'actor_is_group_manager', 'params' : {}},
    ]
    crud = {
        'Group' : {
            'c' : False,
            'r' : ['managers', 'name', 'users'],
            'u' : ['managers', 'name', 'users'],
            'd' : False,
        },
    }
    machine.add_acl_to_role('Group Manager', methods, crud)
