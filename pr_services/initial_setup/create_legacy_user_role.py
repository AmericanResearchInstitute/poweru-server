from decorators import authz

@authz
def setup(machine):
    methods = [
        {'name' : 'actor_is_authenticated', 'params' : {}},
        {'name' : 'actor_owns_payment', 'params' : {}},
        {'name' : 'actor_related_to_domain_affiliation', 'params' : {}},
        {'name' : 'actor_owns_training_unit_authorization', 'params' : {}},
    ]
    crud = {
        'Answer' : {
            'c' : False,
            'r' : ['label'],
            'u' : [],
            'd' : False,
        },
        'Domain' : {
            'c' : False,
            'r' : ['name'],
            'u' : [],
            'd' : False,
        },
        'DomainAffiliation' : {
            'c' : True,
            'r' : ['default', 'domain', 'may_log_me_in', 'user', 'username'],
            'u' : ['default', 'domain', 'may_log_me_in', 'username'],
            'd' : False,
        },
        'SessionTemplate' : {
            'c' : False,
            'r' : ['active', 'version', 'audience', 'description', 'sequence',
                      'duration', 'sessions', 'fullname', 'modality', 'product_line', 'shortname'],
            'u' : [],
            'd' : False,
        },
        'Group' : {
            'c' : False,
            'r' : ['managers', 'name', 'users'],
            'u' : [],
            'd' : False,
        },
        'Organization' : {
            'c': False,
            'r': ['name', 'parent', 'children', 'ancestors', 'descendants'],
            'u': [],
            'd': False,
        },
        'OrgRole' : {
            'c' : False,
            'r' : ['name'],
            'u' : [],
            'd' : False,
        },
        'Payment' : {
            'c' : True,
            'r' : ['refunds', 'card_type', 'exp_date', 'amount',
                      'first_name', 'last_name', 'city', 'state', 'zip', 'country',
                      'sales_tax', 'transaction_id', 'invoice_number', 'result_message',
                      'purchase_order', 'date'],
            'u' : [],
            'd' : False,
        },
        'PurchaseOrder' : {
            'c' : True,
            'r' : [],
            'u' : [],
            'd' : False,
        },
        'ProductClaim' : {
            'c' : True,
            'r' : ['product', 'purchase_order', 'quantity'],
            'u' : ['quantity'],
            'd' : True,
        },
        'SessionUserRoleRequirement' : {
            'c' : False,
            'r' : [],
            'u' : [],
            'd' : False,
        },
        'TrainingUnitAuthorization' : {
            'c' : False,
            'r' : ['training_unit_account', 'user', 'start',
                      'end', 'max_value', 'used_value'],
            'u' : [],
            'd' : False,
        },
        'User' : {
            'c' : False,
            'r' : ['default_username_and_domain',],
            'u' : [],
            'd' : False,
        },
        'Venue' : {
            'c' : False,
            'r' : ['contact', 'region', 'address', 'phone', 'name'],
            'u' : [],
            'd' : False,
        },
    }
    machine.add_acl_to_role('User', methods, crud)
