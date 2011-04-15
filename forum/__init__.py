import facade

facade.managers.add_import('ForumCategoryManager', 'forum.managers')
facade.managers.add_import('ForumManager', 'forum.managers')
facade.managers.add_import('ForumPostAttachmentManager', 'forum.managers')
facade.managers.add_import('ForumPostManager', 'forum.managers')
facade.managers.add_import('ForumTopicManager', 'forum.managers')

facade.models.add_import('ForumCategory', 'forum.models')
facade.models.add_import('Forum', 'forum.models')
facade.models.add_import('ForumPostAttachment', 'forum.models')
facade.models.add_import('ForumPost', 'forum.models')
facade.models.add_import('ForumTopic', 'forum.models')
