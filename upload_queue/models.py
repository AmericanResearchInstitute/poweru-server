from django.db import models
from django.core.files.storage import FileSystemStorage
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class UploadTask(models.Model):
    """This model is used under the hood by queue_upload to temporarily store the file and a 'reference' to the target object."""
    local_file = models.FileField(upload_to='upload_queue/', storage=FileSystemStorage())
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    to_instance = generic.GenericForeignKey()
