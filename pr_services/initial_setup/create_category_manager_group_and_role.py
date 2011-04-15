import facade
from decorators import authz

@authz
def setup(machine):
    group, created = facade.models.Group.objects.get_or_create(
        name='Category Managers')

    methods = [
        {'name' : 'actor_member_of_group', 'params' : {'group_id' : group.id}},
        {'name' : 'actor_is_manager_of_actee_related_category', 'params' : {}},
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
        'Category' : {
            'c' : False,
            'r' : ['authorized_groups', 'locked', 'managers', 'name', 'videos', 'approved_videos'],
            'u' : ['authorized_groups'],
            'd' : False,
        },
        'EncodedVideo' : {
            'c' : False,
            'r' : ['video', 'bitrate', 'url'],
            'u' : [],
            'd' : False,
        },
        'Group' : {
            'c' : False,
            'r' : ['name'],
            'u' : [],
            'd' : False,
        },
        'User' : {
            'c' : False,
            'r' : ['default_username_and_domain', 'username', 'email', 'first_name', 'last_name'],
            'u' : [],
            'd' : False,
        },
        'Video' : {
            'c' : False,
            'r' : ['approved_categories', 'author', 'categories',
                   'category_relationships', 'create_timestamp', 'description',
                   'encoded_videos', 'length', 'live', 'name', 'num_views',
                   'photo_url', 'prerequisite_tasks', 'public',
                   'src_file_size', 'status', 'tags'],
            'u' : ['author', 'categories', 'description',
                   'length', 'live', 'name', 'photo_url',
                   'public', 'tags'],
            'd' : False,
        },
        'VideoCategory' : {
            'c' : True,
            'r' : ['status', 'category', 'category_name', 'video'],
            'u' : ['status'],
            'd' : False,
        },
        'VideoSession' : {
            'c' : False,
            'r' : ['assignment', 'date_started', 'date_completed', 'user', 'video'],
            'u' : [],
            'd' : False,
        },
    }
    machine.add_acl_to_role('Category Manager', methods, crud)
    methods2 = [
        {'name' : 'actor_member_of_group', 'params' : {'group_id' : group.id}},
        {'name' : 'actees_foreign_key_object_has_attribute_set_to',
            'params' : {
                'actee_model_name' : 'VideoCategory',
                'attribute_name' : 'video',
                'foreign_object_attribute_name' : 'deleted',
                'foreign_object_attribute_value' : False,
            }
        },
    ]
    crud2 = {
        'VideoCategory' : {
            'c' : True,
            'r' : ['status', 'category', 'category_name', 'video'],
            'u' : [],
            'd' : False,
        },
    }
    machine.add_acl_to_role('Category Manager', methods2, crud2)
