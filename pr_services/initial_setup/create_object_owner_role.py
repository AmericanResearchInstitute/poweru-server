from decorators import authz

@authz
def setup(machine):
    methods = [
        {'name' : 'actor_has_completed_assignment_prerequisites', 'params' : {}},
        {'name' : 'actor_is_acting_upon_themselves', 'params' : {}},
        {'name' : 'actor_owns_address', 'params' : {}},
        {'name' : 'actor_owns_assignment', 'params' : {}},
        {'name' : 'actor_owns_assignment_attempt', 'params' : {}},
        {'name' : 'actor_owns_credential', 'params' : {}},
        {'name' : 'actor_owns_prmodel', 'params' : {}},
        {'name' : 'actor_owns_question_response', 'params' : {}},
        {'name' : 'assignment_attempt_meets_date_restrictions', 'params' : {}},
        {'name' : 'assignment_attempt_prerequisites_met', 'params' : {}},
        {'name' : 'assignment_is_not_video', 'params' : {}},
        {'name' : 'populated_exam_session_is_finished', 'params' : {}},
    ]
    crud = {
        'Assignment' : {
            'c' : True,
            'r' : ['task', 'task_content_type', 'user', 'date_started',
                   'date_completed', 'due_date', 'prerequisites_met',
                   'effective_date_assigned', 'status', 'assignment_attempts'],
            'u' : [],
            'd' : False,
        },
        'AssignmentAttempt' : {
            'c' : True,
            'r' : ['assignment', 'date_started', 'date_completed'],
            'u' : [],
            'd' : False,
        },
        'Credential' : {
            'c' : False,
            'r' : ['authority', 'credential_type', 'date_assigned',
                   'date_expires', 'date_granted', 'date_started',
                   'serial_number', 'status', 'user'],
            'u' : [],
            'd' : False,
        },
        'ExamSession' : {
            'c' : True,
            'r' : ['id', 'exam', 'score', 'passed', 'date_started',
                   'passing_score', 'number_correct', 'date_completed', 'response_questions'],
            'u' : ['date_completed'],
            'd' : False,
        },
        'Response' : {
            'c' : True,
            'r' : ['exam_session', 'question', 'text', 'value', 'valid'],
            'u' : [],
            'd' : False,
        },
        'ScoSession' : {
            'c' : True,
            'r' : ['date_completed', 'date_started', 'sco'],
            'u' : [],
            'd' : False,
        },
        'User' : {
            # We allow users to create themselves
            'c' : True,
            'r' : ['credentials',
                   'session_user_role_requirements', 'product_lines_managed',
                   'product_lines_instructor_manager_for', 'product_lines_instructor_for',
                   'groups', 'roles', 'photo_url', 'url', 'username',
                   'title', 'first_name', 'middle_name', 'last_name', 'name_suffix',
                   'full_name',
                   'phone', 'phone2', 'phone3', 'email', 'email2',
                   'status', 'color_code', 'biography',
                   'shipping_address', 'billing_address', 'organizations', 'owned_userorgroles',
                   'preferred_venues',
                   'suppress_emails', 'default_username_and_domain', 'alleged_organization'],
            'u' : ['photo_url', 'url',
                   'title', 'first_name', 'middle_name', 'last_name', 'name_suffix',
                   'phone', 'phone2', 'phone3', 'email', 'email2', 'color_code',
                   'biography', 'shipping_address', 'billing_address',
                   'preferred_venues', 'suppress_emails', 'alleged_organization'],
            'd' : False,
        },
        'UserOrgRole' : {
            'c' : False,
            'r' : ['owner', 'organization', 'organization_name', 'role', 'role_name', 'parent', 'children'],
            'u' : [],
            'd' : False,
        },
        'Venue' : {
            'c' : False,
            'r' : ['region', 'address'],
            'u' : [],
            'd' : False,
        },
        'VideoSession' : {
            'c' : True,
            'r' : ['assignment', 'date_started', 'date_completed'],
            'u' : [],
            'd' : False,
        },
    }
    machine.add_acl_to_role('Object Owner', methods, crud)
