from decorators import authz

@authz
def setup(machine):
    methods = [
        {'name' : 'actor_is_product_line_manager_of_session', 'params' : {}},
        {'name' : 'actor_is_product_line_manager_of_session_template', 'params' : {}},
        {'name' : 'actor_is_product_line_manager_of_user', 'params' : {}},
        {'name' : 'actor_is_product_line_manager_of_product_line', 'params' : {}},
    ]
    crud = {
        'ProductLine' : {
            'c' : False,
            'r' : ['name', 'managers', 'instructor_managers', 'instructors'],
            'u' : ['name', 'instructor_managers', 'instructors'],
            'd' : False,
        },
        'Session' : {
            'c' : True,
            'r' : ['default_price', 'room', 'evaluation',
                      'start', 'end', 'session_template', 'name',
                      'audience', 'title', 'confirmed', 'status',
                      'url', 'modality'],
            'u' : [ 'default_price', 'room', 'start', 'end', 'session_template', 'name', 'audience', 'title',
                    'confirmed', 'status', 'url', 'modality'],
            'd' : True,
        },
        'SessionTemplate' : {
            'c' : True,
            'r' : ['shortname', 'fullname', 'version', 'event_template', 'sequence',
                      'description', 'audience', 'price', 'lead_time', 'duration', 'product_line',
                      'modality'],
            'u' : [ 'shortname', 'fullname', 'version', 'description', 'audience', 'price', 'lead_time', 'duration', 'modality', 'event_template', 'sequence',],
            'd' : True,
        },
        'User' : {
            'c' : True,
            'r' : ['last_name', 'phone', 'credentials'],
            'u' : ['last_name', 'phone'],
            'd' : False,
        },
    }
    machine.add_acl_to_role('Product Line Manager', methods, crud)
