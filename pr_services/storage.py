from __future__ import with_statement

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.move import file_move_safe
from django.utils._os import safe_join
from django.utils.text import get_valid_filename
from PIL import Image, ImageFile
import os
import errno
import exceptions
import urlparse
import uuid

class PhotoStorage(FileSystemStorage):
    def _save(self, name, content):
        full_path = self.path(name)

        directory = os.path.dirname(full_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        elif not os.path.isdir(directory):
            raise IOError("%s exists and is not a directory." % directory)

        # There's a potential race condition between get_available_name and
        # saving the file; it's possible that two threads might return the
        # same name, at which point all sorts of fun happens. So we need to
        # try to create the file, but if it already exists we have to go back
        # to get_available_name() and try again.

        while True:
            try:
                # This file has a file path that we can move.
                if hasattr(content, 'temporary_file_path'):
                    file_move_safe(content.temporary_file_path(), full_path)
                    content.close()

                # This is a normal uploadedfile that we can stream.
                else:
                    # This fun binary flag incantation makes os.open throw an
                    # OSError if the file already exists before we open it.
                    try:
                        content.seek(0)
                        image = Image.open(content)
                    except IOError:
                        raise exceptions.InvalidImageUploadException()
                    image_size = (self.PHOTO_MAX_X, self.PHOTO_MAX_Y)
                    image.thumbnail(image_size, Image.ANTIALIAS)
                    image.save(full_path)
            except OSError, e:
                if e.errno == errno.EEXIST:
                    # Ooops, the file exists. We need a new file name.
                    name = self.get_available_name(name)
                    full_path = self.path(name)
                else:
                    raise
            else:
                # OK, the file save worked. Break out of the loop.
                break
        
        if settings.FILE_UPLOAD_PERMISSIONS is not None:
            os.chmod(full_path, settings.FILE_UPLOAD_PERMISSIONS)
        
        return name

    def get_valid_name(self, name):
        """Run the name through Django's validator, just in case"""
        return get_valid_filename(name)
        
    def get_available_name(self, name):
        """Generate a filename based on UUID with the preferred image extension"""
        # uuid4() returns a randomly generated v4 UUID, per RFC 4122
        filename = str(uuid.uuid4()) + '.' + settings.PHOTO_FORMAT
        return filename

class UserPhotoStorage(PhotoStorage):
    def __init__(self, location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL):
        self.base_url = urlparse.urljoin(base_url, settings.USER_PHOTO_PATH).replace('\\', '/')
        self.location = safe_join(location, settings.USER_PHOTO_PATH)
        self.PHOTO_MAX_X = settings.USER_PHOTO_MAX_X
        self.PHOTO_MAX_Y = settings.USER_PHOTO_MAX_Y

class OrganizationPhotoStorage(PhotoStorage):
    def __init__(self, location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL):
        self.base_url = urlparse.urljoin(base_url, settings.ORG_PHOTO_PATH).replace('\\', '/')
        self.location = safe_join(location, settings.ORG_PHOTO_PATH)
        self.PHOTO_MAX_X = settings.ORG_PHOTO_MAX_X
        self.PHOTO_MAX_Y = settings.ORG_PHOTO_MAX_Y

class FormPagePhotoStorage(PhotoStorage):
    def __init__(self, location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL):
        self.base_url = urlparse.urljoin(base_url, settings.FORM_PAGE_PHOTO_PATH).replace('\\', '/')
        self.location = safe_join(location, settings.FORM_PAGE_PHOTO_PATH)
        self.PHOYO_MAX_X = settings.FORM_PAGE_PHOTO_MAX_X
        self.PHOYO_MAX_Y = settings.FORM_PAGE_PHOTO_MAX_Y

# vim:tabstop=4 shiftwidth=4 expandtab
