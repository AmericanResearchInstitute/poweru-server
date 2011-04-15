import facade
from decorators import authz

@authz
def setup(machine):
    group, created = facade.models.Group.objects.get_or_create(name='Students')

    methods_1 = [
        {'name' : 'actor_member_of_group', 'params' : {'group_id' : group.id}},
    ]
    crud_1 = {
        'Sco' : {
            'c' : False,
            'r' : ['course', 'description', 'name',
                   'prerequisite_tasks', 'type',
                   'version_id', 'version_label',],
            'u' : [],
            'd' : False,
        },
        'Task' : {
            'c' : False,
            'r' : ['description', 'name', 'prerequisite_tasks',
                   'type', 'version_id', 'version_label',],
            'u' : [],
            'd' : False,
        },
    }
    machine.add_acl_to_role('Student', methods_1, crud_1)

    methods_2 = [
        {'name' : 'actor_has_completed_task_prerequisites', 'params' : {}},
    ]
    crud_2 = {
        'Sco' : {
            'c' : False,
            'r' : ['url'],
            'u' : [],
            'd' : False,
        },
    }
    machine.add_acl_to_role('Student', methods_2, crud_2)
