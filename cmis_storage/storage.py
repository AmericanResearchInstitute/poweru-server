"""
@author Sean Myers <smyers@americanri.com>
@copyright Copyright 2008 American Research Institute, Inc.
"""

import os
import uuid
import urlparse

from django.conf import settings
from django.core.files.storage import Storage

__all__ = ('CMISStorage',)

class CMISStorage(Storage):
    """
    A storage system that uses CMIS as a backend via SOAP bindings.
    """

    # I'm not sure how the next two methods will be relevant to CMIS, since
    # my hope is to reference files using alfresco's built-in UUIDs. That makes the
    # file "name" just some easily escapable metadata. As far as I can tell, CMIS
    # doesn't allow you to specify UUID on create, but it can use them later on to refer
    # to existing content (which I plan to do)
    def get_valid_name(self, name):
        """
        Returns a filename, based on the provided filename, that's suitable for
        use in the target storage system.
        """
        return name

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        return name

    def path(self, name):
        """
        This storage systems can't be accessed using builtin open(), and 
        does not implement this method.
        """
        raise NotImplementedError("This backend doesn't support absolute paths.")

    # These are the workhorse methods, which will likely see the most use

    def _open(self, name, mode=None):
        """
        Returns a file-like object representing the CMIS content.
        """
        # read method on Content Web Service
        raise NotImplementedError()

    def _save(self, name, content):
        """
        Saves the provided content to the CMIS backend.
        """
        # write method on Content Web Service
        raise NotImplementedError()

    # The following methods form the public API for storage systems, but with
    # no default implementations. Subclasses must implement *all* of these.

    def delete(self, name):
        """
        Deletes the specified file from the storage system.
        """
        # delete method on Content Web Service
        raise NotImplementedError()

    def exists(self, name):
        """
        Returns True if a file referened by the given name already exists in the
        storage system, or False if the name is available for a new file.
        """
        # exists method on Content Web Service
        raise NotImplementedError()

    def listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple of lists;
        the first item being directories, the second item being files.
        """
        # list method of the FileSystem Web Service
        raise NotImplementedError()

    def size(self, name):
        """
        Returns the total size, in bytes, of the file specified by name.
        """
        # describe method of the Content Web Service
        raise NotImplementedError()

    def url(self, name):
        """
        Returns an absolute URL where the file's contents can be accessed
        directly by a web browser.
        """
        # This one's messy, where we likely need a web script or something to 
        # generate this URL for temporary anonymous access to files that would 
        # otherwise need authorization. As this is *the* method which will make
        # This entire app useful, it's a good idea to figure this one out.
        raise NotImplementedError()

