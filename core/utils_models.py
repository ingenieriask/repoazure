from uuid import uuid4
from django.utils.deconstruct import deconstructible
from django.core.files.storage import FileSystemStorage
from django.conf import settings

import os

@deconstructible
class UploadToPathAndRename(object):

    def __init__(self, path):
        self.sub_path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # define filename
        filename = 'logo.{}'.format(ext)
        # return the whole path to the file
        return os.path.join(self.sub_path, filename)

class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name, max_length=None):
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name