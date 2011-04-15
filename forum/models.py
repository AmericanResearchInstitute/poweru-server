from django.db import models
from pr_services import models as pr_models

class Forum(models.Model):
    categories = models.ManyToManyField('ForumCategory', related_name='forums')
    name = models.CharField(max_length=127, unique=True)
    description = models.TextField()
    blame = pr_models.PRForeignKey(pr_models.Blame)

class ForumTopic(models.Model):
    forum = pr_models.PRForeignKey('Forum', related_name='topics')
    name = models.CharField(max_length=127)
    sticky = pr_models.PRBooleanField(default=False)
    closed = pr_models.PRBooleanField(default=False)
    blame = pr_models.PRForeignKey(pr_models.Blame)

class ForumPost(models.Model):
    user = pr_models.PRForeignKey(pr_models.User, related_name='posts')
    topic = pr_models.PRForeignKey('ForumTopic', related_name='posts')
    body = models.TextField()
    blame = pr_models.PRForeignKey(pr_models.Blame)

class ForumPostAttachment(models.Model):
    post = pr_models.PRForeignKey('ForumPost', related_name='attachments')
    name = models.CharField(max_length=255)
    description = models.TextField()
    attachment = models.FileField(upload_to='forum')

class ForumCategory(models.Model):
    name = models.CharField(max_length=127, unique=True)
    blame = pr_models.PRForeignKey(pr_models.Blame)

