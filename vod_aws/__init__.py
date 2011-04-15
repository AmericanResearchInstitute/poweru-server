import facade

# register our managers
facade.managers.add_import('CategoryManager','vod_aws.managers')
facade.managers.add_import('VideoCategoryManager','vod_aws.managers')
facade.managers.add_import('EncodedVideoManager','vod_aws.managers')
facade.managers.add_import('VideoManager', 'vod_aws.managers')
facade.managers.add_import('VideoSessionManager', 'vod_aws.managers')

# register our models
facade.models.add_import('Category', 'vod_aws.models')
facade.models.add_import('VideoCategory', 'vod_aws.models')
facade.models.add_import('EncodedVideo', 'vod_aws.models')
facade.models.add_import('Video', 'vod_aws.models')
facade.models.add_import('VideoSession', 'vod_aws.models')

# register our authorizer, overriding the one currently on the facade
facade.subsystems.override('Authorizer', 'vod_aws.authorizer')
