from decorators import authz

@authz
def setup(machine):
    methods = [
        {'name' : 'actor_is_member_of_actee_related_category_authorized_groups', 'params' : {}},
        {'name' : 'actor_owns_assignment', 'params' : {}}
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
            'r' : ['name', 'locked', 'approved_videos'],
            'u' : [],
            'd' : False,
        },
        'EncodedVideo' : {
            'c' : False,
            'r' : ['video', 'bitrate', 'url'],
            'u' : [],
            'd' : False,
        },
        'Video' : {
            'c' : False,
            'r' : ['approved_categories', 'author', 'create_timestamp',
                   'description', 'encoded_videos', 'length', 'live', 'name',
                   'num_views', 'photo_url', 'prerequisite_tasks', 'public',
                   'src_file_size', 'tags'],
            'u' : [],
            'd' : False,
        },
    }
    machine.add_acl_to_role('Video Watcher', methods, crud)
