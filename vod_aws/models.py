import awsutils
import copy
import urllib
from datetime import datetime
from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import fastenc
from pr_services import models as pr_models
from pr_services import exceptions
from pr_services import storage
from storages.backends.s3boto import S3BotoStorage
import tagging
from pr_services import pr_time
import facade

class Video(pr_models.Task):
    """This is a user Task to view a video.

    The actual video files that Users will view are represented by the
    EncodedVideo model, which stores the URLs to each of the videos along with
    their encoding bitrate.

    """
    ASPECT_RATIO_CHOICES = [
        ('4:3', '4:3'),
        ('16:9', '16:9'),
    ]
    # Store the aspect ratio of the video
    aspect_ratio = models.CharField(max_length=4, choices=ASPECT_RATIO_CHOICES)
    author = models.CharField(max_length=128)
    #: The category that this Video should appear in
    categories = models.ManyToManyField('Category', related_name='videos', through='VideoCategory')
    #: An intifier that Encoding.com returns for an encoding job
    encoding_job_mediaid = models.CharField(max_length=38)
    #: The length of the Video, in HH:MM:SS format
    length = models.CharField(max_length=8)
    #: Whether the video is live (True) or on demand (False)
    live = pr_models.PRBooleanField(default=False)
    #: You can retrieve the photo itself by calling user.photo, but more likely
    #: you want user.photo_url to pass to the client.
    photo = models.FileField(upload_to='video/', storage=S3BotoStorage())
    #: The src video file as stored in Amazon S3.
    src_file = models.FileField(upload_to='video/', storage=S3BotoStorage())
    #: The size of the uploaded file
    src_file_size = models.PositiveIntegerField(null=True)
    #: Gets set to true after the photo and encoded_videos are populated
    is_ready = pr_models.PRBooleanField(default=False)
    deleted = pr_models.PRBooleanField(default=False)

    @property
    def status(self):
        if self.deleted:
            return 'deleted'
        cat_status = set(self.category_relationships.values_list('status', flat=True))
        if 'approved' in cat_status:
            return 'approved'
        if 'pending' in cat_status:
            return 'pending'
        return 'rejected'

    @property
    def photo_url(self):
        """
        Returns the URL the thumbnail for this video can be fetched from.
        """
        try:
            photo_file = self.photo.file
        except (ValueError, IOError):
            return settings.MEDIA_URL + settings.VOD_TEMP_THUMBNAIL
        else:
            return photo_file.key.generate_url(settings.AWS_URL_LIFETIME)

    @property
    def approved_categories(self):
        approved = filter(lambda cr: cr.status == 'approved',
            self.category_relationships.all())
        return [cr.category.id for cr in approved]

    def _get_num_views(self, start_date=None, end_date=None):
        """Returns the number of VideoSession objects that are associated with this Video object, optionally filtered by start and end dates."""

        session_filter = {'assignment__task__id__exact' : self.id}
        if start_date is not None:
            if pr_time.is_iso8601(start_date):
                start_date = pr_time.iso8601_to_datetime(start_date)
            session_filter['date_started__gte'] = start_date
        if end_date is not None:
            if pr_time.is_iso8601(end_date):
                end_date = pr_time.iso8601_to_datetime(end_date)
            session_filter['date_started__lte'] = end_date
        return VideoSession.objects.filter(**session_filter).count()
    #: The number of times this video has been viewed
    num_views = property(_get_num_views)

    def _get_users_who_watched(self):
        """
        Returns a list of the primary keys of the User objects that this Video has VideoSession objects for.
        """

        user_keys_list = facade.models.User.objects.filter(assignments__task__id__exact=self.id).values_list('id', flat=True)
        # Let's use a set to make this list unique
        user_keys_set = set(user_keys_list)
        return list(user_keys_set)

    #: A list of primary keys of User objects that have watched this Video
    users_who_watched = property(_get_users_who_watched)

try:
    tagging.register(Video)
except tagging.AlreadyRegistered:
    pass


class Category(pr_models.PRModel):
    name = models.CharField(max_length=31, null=False)
    managers = models.ManyToManyField(pr_models.User, related_name='categories')
    authorized_groups = models.ManyToManyField(pr_models.Group, related_name='categories')
    locked = pr_models.PRBooleanField(default=False)

    @property
    def approved_videos(self):
        approved = filter(lambda cr: cr.status == 'approved',
            self.video_relationships.all())
        return [cr.video.id for cr in approved]

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class VideoCategory(pr_models.PRModel):
    video = pr_models.PRForeignKey(Video, related_name='category_relationships')
    category = pr_models.PRForeignKey(Category, related_name='video_relationships')
    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('approved', 'approved'),
        ('rejected', 'rejected'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    def validate(self, validation_errors=None):
        if validation_errors is None:
            validation_errors = dict()
        if not self.id and self.category.locked:
            if not validation_errors.has_key('category'):
                validation_errors['category'] = list()
            validation_errors['category'].append(
                u"Can't add Video to locked Category")
        return super(VideoCategory, self).validate(validation_errors)

    @property
    def category_name(self):
        return self.category.name

    def __unicode__(self):
        return '%s : %s' % (self.video, self.category)

    class Meta:
        ordering = ('id',)
        unique_together = ('video', 'category')


class EncodedVideo(pr_models.OwnedPRModel):
    """This is a user Task to view a video."""

    #: used to make the encoding.com job request
    audio_codec = models.CharField(max_length=31, null=False)
    #: The bitrate of the EncodedVideo, in kilobytes per second
    bitrate = models.CharField(max_length=31, null=False)
    #: used to make the encoding.com job request
    output = models.CharField(max_length=31)
    #: used to make the encoding.com job request
    size = models.CharField(max_length=15)
    #: The video that this encoding is for
    video = pr_models.PRForeignKey(Video, null=False, related_name='encoded_videos')
    # Different codecs can result in different stream URLs,
    # so capture the codec for when those URLs are generated
    video_codec = models.CharField(max_length=31)
    #: Represents the encoded video stored in S3
    file = models.FileField(upload_to='video/', storage=S3BotoStorage())

    @property
    def http_url(self):
        if self.file.name:
            return self.file.url

    @property
    def url(self):
        if self.file.name:
            return awsutils.CloudFrontStreamingObject(self.file.name).generate_url()

    class Meta:
        ordering = ('id',)

class VideoSession(pr_models.AssignmentAttempt):
    """This represents a session of a User watching a Video."""

    @property
    def video(self):
        video = self.assignment.task.downcast_completely()
        if isinstance(video, Video):
            return video
        else:
            raise TypeError('Assigned Task is not a Video')
    
    @property
    def user(self):
        return self.assignment.user

    def save(self, *args, **kwargs):
        if self.pk == None:
            self.date_completed = datetime.utcnow()
        super(VideoSession, self).save(*args, **kwargs)
