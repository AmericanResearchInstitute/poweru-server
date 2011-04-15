# Django settings for power_reg project.

from datetime import timedelta
import logging
import logging.handlers
import os
import sys
import tempfile
from django.conf import global_settings

# Update this module's local settings from the global settings module.
this_module = sys.modules[__name__]
for setting in dir(global_settings):
    if setting == setting.upper():
        setattr(this_module, setting, getattr(global_settings, setting))

# A useful variable for building filesystem paths relative to the project root
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = '4kyb8+#m4)yrn98u2(s1ct3%im$cfwiwwo!&er@hcyh8zdxiz('

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    #'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.middleware.doc.XViewMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'pr_services.middleware.ThreadLocal',
)

# A cache backend that shares data across processes is required for the upload
# progress bar to work.  In this case, create a file-based cache in the system
# temp directory.
CACHE_BACKEND = 'file://%s' % os.path.join(tempfile.gettempdir(), \
    'upload-progress-cache' + str(hash(os.path.abspath(__file__))))

FILE_UPLOAD_HANDLERS = ('pr_services.utils.upload.UploadProgressCachedHandler',) + \
    global_settings.FILE_UPLOAD_HANDLERS

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'templates').replace('\\','/'),
    os.path.join(PROJECT_ROOT, 'pr_services/scorm_system/templates').replace('\\','/'),
)

# The order in INSTALLED_APPS is important!  Plugins for pr_services depend on
# being initialized after pr_services.  At the time of this writing, the only
# plugin that expects this is vod_aws.
INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'tagging',
    'pr_services',
    #'ecommerce',
    'vod_aws',
    'upload_queue',
    #'gilmore',
    'forum',
    'south',
    'djcelery',
    'pr_messaging',
)

# List of apps to be skipped when running unit tests (see pr_services.__init__.py).
TEST_SKIP_APP_TESTS = (
    'django.contrib.contenttypes',
    'tagging',
    'south',
    'djcelery',
)

# django-celery requires this
import djcelery
djcelery.setup_loader()

# recurring tasks, run by celerybeat
CELERYBEAT_SCHEDULE = {
    'expire_old_credentials' : {
        'task' : 'pr_services.tasks.expire_old_credentials',
        'schedule' : timedelta(days=1),
    },
    'remove_old_auth_tokens': {
        'task' : 'pr_services.tasks.remove_old_auth_tokens',
        'schedule' : timedelta(seconds=(60 * 60)), #every hour
    },
    'process_completed_sessions': {
        'task' : 'pr_services.tasks.process_completed_sessions',
        'schedule' : timedelta(seconds=(60 * 60)), #every hour
    },
    #'cleanup_paypal_ec_tokens' : {
    #    'task' : 'pr_services.tasks.cleanup_paypal_ec_tokens',
    #    'schedule' : 'FIXME: there was no schedule in the AsynchronousProcessor',
    #},
    #'process_session_reminders' : {
    #    'task' : 'pr_services.tasks.process_session_reminders',
    #    'schedule' : 'FIXME: there was no schedule in the AsynchronousProcessor',
    #},
}

# Define a custom TRACE log level and Logger class with a trace() method.
logging.addLevelName(5, 'TRACE')
setattr(logging, 'TRACE', 5)
class Logger(logging.Logger):
    def trace(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.TRACE):
            self._log(logging.TRACE, msg, args, **kwargs)
logging.setLoggerClass(Logger)

## The following USER_PHOTO_* options should not be left to the whim of the
## local administrator.
# extension for one of PIL's writable formats, generally one of 
# (gif, jpg, png)
# See http://www.pythonware.com/library/pil/handbook/index.htm for complete list
PHOTO_FORMAT = 'png'

# Local file path, relative to the MEDIA_ROOT, where user photos will be stored.
# USER_PHOTO_PATH must end with a slash!
USER_PHOTO_PATH = 'user/photo/'

# Max file dimensions; image will be scaled to fit into a bounding box of
# this size, in pixels, while maintaining the original aspect ratio.
USER_PHOTO_MAX_X = 64
USER_PHOTO_MAX_Y = 64

# Local file path, relative to the MEDIA_ROOT, where user photos will be stored.
# ORG_PHOTO_PATH must end with a slash!
ORG_PHOTO_PATH = 'organization/photo/'

# Max file dimensions; image will be scaled to fit into a bounding box of
# this size, in pixels, while maintaining the original aspect ratio.
ORG_PHOTO_MAX_X = 64
ORG_PHOTO_MAX_Y = 64

# Local file path, relative to the MEDIA_ROOT, where user photos will be stored.
# FORM_PAGE_PHOTO_PATH must end with a slash!
FORM_PAGE_PHOTO_PATH = 'form_page/image/'

# Max file dimensions; image will be scaled to fit into a bounding box of
# this size, in pixels, while maintaining the original aspect ratio.
FORM_PAGE_PHOTO_MAX_X = 64
FORM_PAGE_PHOTO_MAX_Y = 64

# This is the path where SCORM courses should be stored after they are uploaded and accepted, relative to SECURE_MEDIA_ROOT
# The courses will be in separate folders by their primary keys
COURSE_PATH = 'course/id/'

# This tells the unit tests that this is PowerReg core
IS_POWER_REG_CORE = True

#: force tags to lower case
FORCE_LOWERCASE_TAGS = True

## AWS VOD settings

# user id for encoding.com
AWS_ENCODING_OAI_S3_USER = '1a85ad8fea02b4d948b962948f69972a72da6bed800a7e9ca7d0b43dc61d5869'

# things we upload should not be readable by others
AWS_DEFAULT_ACL = 'private'

# Include any local settings that override the defaults.
try:
    local_settings_path = os.path.join(PROJECT_ROOT, 'local_settings.py')
    execfile(local_settings_path)
    # Hack so that autoreload will detect changes to local_settings.py.
    class dummymodule(str):
        __file__ = property(lambda self: self)
    sys.modules['local_settings'] = dummymodule(local_settings_path)
except IOError:
    pass

# Fixup any settings imported from local settings.
if not MANAGERS and ADMINS:
    MANAGERS = ADMINS

if isinstance(LOGLEVEL, basestring):
    LOGLEVEL = logging.getLevelName(LOGLEVEL)

# Include the WatchedFileHandler implementation from Python >= 2.6 if we happen
# to be running on Python 2.5
try:
    from logging.handlers import WatchedFileHandler2
except ImportError:
    import stat as _stat
    class WatchedFileHandler(logging.FileHandler):
        def __init__(self, filename, mode='a', encoding=None):
            logging.FileHandler.__init__(self, filename, mode, encoding)
            if not os.path.exists(self.baseFilename):
                self.dev, self.ino = -1, -1
            else:
                stat = os.stat(self.baseFilename)
                self.dev, self.ino = stat[_stat.ST_DEV], stat[_stat.ST_INO]
        def emit(self, record):
            if not os.path.exists(self.baseFilename):
                stat = None
                changed = 1
            else:
                stat = os.stat(self.baseFilename)
                changed = (stat[_stat.ST_DEV] != self.dev) or (stat[_stat.ST_INO] != self.ino)
            if changed and self.stream is not None:
                self.stream.flush()
                self.stream.close()
                self.stream = self._open()
                if stat is None:
                    stat = os.stat(self.baseFilename)
                self.dev, self.ino = stat[_stat.ST_DEV], stat[_stat.ST_INO]
            logging.FileHandler.emit(self, record)

# Disable django 1.3's built-in logging configurator, we are doing it ourselves
LOGGING_CONFIG = None

# Create a TimedRotatingFileHandler instead of a normal FileHandler when the
# LOGFILE_ROTATE_* settings are present.
if len(logging.getLogger().handlers) == 0:
    LOGFILE_ROTATE_WHEN = locals().get('LOGFILE_ROTATE_WHEN')
    LOGFILE_ROTATE_INTERVAL = locals().get('LOGFILE_ROTATE_INTERVAL')
    LOGFILE_ROTATE_BACKUP_COUNT = locals().get('LOGFILE_ROTATE_BACKUP_COUNT')
    if LOGFILE_ROTATE_WHEN or LOGFILE_ROTATE_INTERVAL:
        handler = logging.handlers.TimedRotatingFileHandler(LOGFILE_LOCATION,
            LOGFILE_ROTATE_WHEN or 'h', LOGFILE_ROTATE_INTERVAL or 1,
            LOGFILE_ROTATE_BACKUP_COUNT or 0)
    else:
        handler = WatchedFileHandler(LOGFILE_LOCATION, 'a')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s PID %(process)d TID %(thread)d: %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(LOGLEVEL)

# Add additional error logging to admins using the pr_messaging app.
from pr_messaging.logger import MessagingHandler
# Only executes this part once when settings is imported as 'settings'.
if '.' not in __name__:
    handler = MessagingHandler(level=logging.ERROR, message_type='log-message',
                               recipients=ADMINS)
    logging.getLogger().addHandler(handler)

# vim:tabstop=4 shiftwidth=4 expandtab
