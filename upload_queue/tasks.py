import django.db.models
from upload_queue import models
from celery.decorators import task
from celery.task.sets import subtask

@task(max_retries=5, ignore_result=True)
def upload_file(upload_task_id, to_property, to_path, callback=None, **kwargs):
    """Celery task that uploads a file."""
    task = models.UploadTask.objects.get(pk=upload_task_id)
    field = getattr(task.to_instance, to_property)
    try:
        if field.name: field.delete()
        field.save(to_path, task.local_file.file)
    except Exception, exc:
        upload_file.retry(args=[upload_task_id, to_property, to_path, callback], kwargs=kwargs, exc=exc)
    task.local_file.delete()
    task.delete()
    if callback:
        subtask(callback).delay()

class PendingUpload(object):
    def __init__(self, upload_task_id, to_property, to_path, callback=None):
        self.upload_task_id = upload_task_id
        self.to_property = to_property
        self.to_path = to_path
        self.callback = callback
    def queue(self):
        upload_file.delay(self.upload_task_id, self.to_property, self.to_path, callback=self.callback)

def prepare_upload(to_instance, to_property, to_path, src_file, callback=None):
    """
    Call this function to prepare to schedule an upload to be performed
    asynchronously, with retries; you can optionally specify a callback to
    call when the upload is complete. You need to save the return value and
    call .queue() on it after you've committed; if you're not running in a
    transaction, you should use queue_upload instead.
    
    :param to_instance: django model instance to upload the file to
    :type to_instance: django.db.models.Model
    :param to_property: name of the FileField property of to_instance to upload to
    :type to_property: str
    :param to_path: path which will be given to FieldFile.save()
    :type to_path: str
    :param src_file: file to upload
    :type src_file: django.core.files.File
    :param callback: optional subtask to call when the upload is complete
    :type callback: celery.task.sets.subtask
    :return: returns an object you need to call .queue() on after you've committed the current transaction
    """
    # we want to raise an esception early if the attribute doesn't exist
    field = to_instance._meta.get_field(to_property)
    if not isinstance(field, django.db.models.FileField):
        raise TypeError("queue_upload: can only upload to a FileField")

    task = models.UploadTask.objects.create(to_instance=to_instance)
    task.local_file.save(str(task.id), src_file)
    return PendingUpload(task.id, to_property, to_path, callback=callback)

def queue_upload(to_instance, to_property, to_path, src_file, callback=None):
    """
    Call this function to schedule an upload to be performed asynchronously,
    with retries; you can optionally specify a callback to call when the
    upload is complete. If you are running in a transaction, you want to
    use prepare_upload instead, save it's return value, and call .queue()
    on that after you've committed.
    
    :param to_instance: django model instance to upload the file to
    :type to_instance: django.db.models.Model
    :param to_property: name of the FileField property of to_instance to upload to
    :type to_property: str
    :param to_path: path which will be given to FieldFile.save()
    :type to_path: str
    :param src_file: file to upload
    :type src_file: django.core.files.File
    :param callback: optional subtask to call when the upload is complete
    :type callback: celery.task.sets.subtask
    """
    prepare_upload(to_instance, to_property, to_path, src_file, callback=callback).queue()
