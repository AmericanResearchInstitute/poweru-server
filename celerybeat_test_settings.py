# this is a settings file that we can pass to celerybeat for testing
# it loads the usual one, and then overrides CELERYBEAT_SCHEDULE

import os
PROJECT_ROOT=os.path.abspath(os.path.dirname(__file__))
execfile(os.path.join(PROJECT_ROOT, 'settings.py'))

CELERYBEAT_SCHEDULE = {
    'expire_old_credentials' : {
        'task' : 'pr_services.tasks.expire_old_credentials',
        'schedule' : timedelta(seconds=1),
    },
    'remove_old_auth_tokens': {
        'task' : 'pr_services.tasks.remove_old_auth_tokens',
        'schedule' : timedelta(seconds=1),
    },
    'process_completed_sessions': {
        'task' : 'pr_services.tasks.process_completed_sessions',
        'schedule' : timedelta(seconds=1),
    },
}
