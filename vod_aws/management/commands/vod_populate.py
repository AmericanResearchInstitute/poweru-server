from __future__ import with_statement

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option
import facade
import os
import random

class Command(BaseCommand):
    requires_model_validation = False

    option_list = BaseCommand.option_list + (
        make_option('--num-categories', dest='num_categories', type='int',
            default=25),
        make_option('--videos-per-cat', dest='videos_per_cat', type='int',
            default=4),
        make_option('--users-per-cat', dest='users_per_cat', type='int',
            default=40),
    )
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        self.category_manager = facade.managers.CategoryManager()
        self.encoded_video_manager = facade.managers.EncodedVideoManager()
        self.group_manager = facade.managers.GroupManager()
        self.user_manager = facade.managers.UserManager()
        self.video_category_manager = facade.managers.VideoCategoryManager()
        self.video_manager = facade.managers.VideoManager()

        self.admin_token = facade.subsystems.Utils.get_auth_token_object(
            self.user_manager.login('admin', 'admin')['auth_token'])
        self.cm_role = facade.models.OrgRole.objects.get(name='ContentManager')
        self.user_role = facade.models.OrgRole.objects.get(name='User')
        self.cm_group = facade.models.Group.objects.get(name='Category Managers')
        self.gencache = {}
        self.catcount = 0
        self.videocount = 0

    def make_generator(self, what):
        if what == 'shipping_address' or what == 'billing_address':
            def generator():
                return self.generate('label', 'locality', 'postal_code',
                    'country', 'region')
            return generator
        elif what == 'postal_code':
            def generator():
                return '%05d' % random.randrange(100000)
            return generator
        elif what == 'phone':
            def generator():
                digits = tuple(random.randrange(10) for i in range(10))
                return '%d%d%d-%d%d%d-%d%d%d%d' % digits
            return generator
        elif what == 'orgid':
            list_of_choices = list(
                facade.models.Organization.objects.values_list('id', flat=True))
        else:
            path = os.path.join(settings.PROJECT_ROOT, 'vod_aws', 'test_data',
                'pop_data', what)
            try:
                with open(path, 'r') as f:
                    list_of_choices = [l.strip() for l in f.readlines()]
            except:
                list_of_choices = None

        if isinstance(list_of_choices, list):
            def generator():
                return random.choice(list_of_choices)
        else:
            counter = [0] # I just love python
            def generator():
                counter[0] += 1
                return 'foo%04d%04d' % (counter[0], random.randrange(10000))
        return generator

    def get_generator(self, what):
        if not self.gencache.has_key(what):
            self.gencache[what] = self.make_generator(what)
        return self.gencache[what]

    def generate(self, *args):
        return dict(((arg, self.get_generator(arg)()) for arg in args))

    def create_user(self, username=None, groups=None, roles=None):
        kwargs = self.generate('title', 'first_name', 'last_name', 'phone')
        kwargs['optional_attributes'] = self.generate('shipping_address',
            'billing_address')
        if not username:
            username = self.user_manager.generate_username('',
                kwargs['first_name'], kwargs['last_name'])
        if groups:
            kwargs['optional_attributes']['groups'] = groups
        if roles:
            kwargs['optional_attributes']['roles'] = roles
        email = username+'@test.poweru.net'
        return self.user_manager.create(self.admin_token, username, 'password',
            email=email, status='active', **kwargs).id

    def create_approved_video(self, cat_id):
        self.videocount += 1
        video = self.video_manager.create(self.admin_token,
            'video%04d' % self.videocount, self.get_generator('description')(),
            categories=[cat_id])
        vc = self.video_category_manager.get_filtered(self.admin_token,
            {'exact' : {'video' : video.id, 'category' : cat_id}})[0]['id']
        self.video_category_manager.update(self.admin_token, vc,
            {'status' : 'approved'})
        facade.models.EncodedVideo.objects.create(video=video, output='fl9',
            bitrate='256k', size='320x180', audio_codec='libfaac')
        facade.models.EncodedVideo.objects.create(video=video, output='fl9',
            bitrate='512k', size='640x360', audio_codec='libfaac')
        facade.models.EncodedVideo.objects.create(video=video, output='fl9',
            bitrate='2048k', size='1280x720', audio_codec='libfaac')

    def create_category(self, orgid, videos=1, users=1):
        self.catcount += 1
        manager = self.create_user(username=('manager%04d' % self.catcount),
            groups=[self.cm_group.id],
            roles=[{'id' : self.cm_role.id, 'organization' : orgid}])
        group = self.group_manager.create(self.admin_token,
            'group%04d' % self.catcount)
        cat = self.category_manager.create(self.admin_token,
            'cat%04d' % self.catcount)
        self.category_manager.update(self.admin_token, cat.id, {
            'authorized_groups' : [group.id],
            'managers' : [manager]})
        for i in xrange(users):
            self.create_user(username=('cat%04duser%04d' % (self.catcount, i)),
                roles=[{'id' : self.user_role.id, 'organization' : orgid}],
                groups=[group.id])
        for i in xrange(videos):
            self.create_approved_video(cat.id)

    @transaction.commit_on_success
    def handle(self, *args, **options):
        orgidgen = self.get_generator('orgid')
        for i in xrange(options['num_categories']):
           self.create_category(orgidgen(), options['videos_per_cat'],
               options['users_per_cat'])
