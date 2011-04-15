# -*- coding: utf-8 -*-
"""
non-RPC unit tests for Forums
"""

from pr_services.initial_setup import InitialSetupMachine
import django.test
import settings
import facade

class TestCase(django.test.TransactionTestCase):
    """
    super-class used to do basic setup for pretty much all
    power reg test cases.
    """

    def setUp(self):
        # Initial Setup
        initial_setup_args = getattr(self, 'initial_setup_args', [])
        initial_setup_kwargs = getattr(self, 'initial_setup_kwargs', {})
        InitialSetupMachine().initial_setup(*initial_setup_args, **initial_setup_kwargs)

        # Instantiate Managers
        self.user_manager = facade.managers.UserManager()
        self.attachment_manager = facade.managers.ForumPostAttachmentManager()
        self.category_manager = facade.managers.ForumCategoryManager()
        self.forum_manager = facade.managers.ForumManager()
        self.post_manager = facade.managers.ForumPostManager()
        self.topic_manager = facade.managers.ForumTopicManager()

        # Snag an auth token
        self.admin_token = facade.models.AuthToken.objects.get(session_id=self.user_manager.login('admin', 'admin')['auth_token'])

        # TODO: We used to have an "ordinary guy" auth token that was never
        #  used, but having some tests using a non-admin role would be good

class TestForum(TestCase):
    def test_forum_creation(self):
        category1 = self.category_manager.create(self.admin_token, 'Stuff')
        category2 = self.category_manager.create(self.admin_token, 'Things')

        forum = self.forum_manager.create(self.admin_token, 'Interesting Matters', [category1.id, category2.id])

        topic = self.topic_manager.create(self.admin_token, 'Advice on Taking Over the World', forum.id)

        body = """I have been considering taking over the world.  I think it could
make a fun weekend project!  Not to mention, it will be a good excuse to buy some
new power tools.  Any advice from the world-domination gurus?

Thanks!"""

        post = self.post_manager.create(self.admin_token, body, topic.id)

        attachment = self.attachment_manager.create(self.admin_token, 'World Map', post.id)
