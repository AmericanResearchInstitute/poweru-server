from decorators import authz

@authz
def setup(machine):
    methods = [
        {'name' : 'actor_is_member_of_any_organization', 'params' : {}},
        # the below 2 are here to prevent everyone from seeing Videos in the
        # system unless they absolutely have to in order for uploads to work
        {'name' : 'actor_owns_prmodel', 'params' : {}},
        {'name' : 'actees_attribute_is_set_to',
            'params' : {
                'actee_model_name' : 'Video',
                'attribute_name' : 'deleted',
                'attribute_value' : False
            }
        },
    ]
    crud = {
        'Category' : {
            'c' : False,
            'r' : ['name', 'locked'],
            'u' : [],
            'd' : False,
        },
        'Video' : {
            'c' : True,
            'r' : [],
            'u' : [],
            'd' : False,
        },
    }
    machine.add_acl_to_role('Video Uploader', methods, crud)
