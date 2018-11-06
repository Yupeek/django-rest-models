# -*- coding: utf-8 -*-
import datetime
import logging
import os
import threading

from django.core.files import File
from django.core.files.storage import Storage

logger = logging.getLogger(__name__)


class ExpirableDict(object):

    def __init__(self, maxage=datetime.timedelta(hours=1)):
        self.pool = {}
        self.maxage = maxage
        self.rlock = threading.RLock()

    def _clean_cache(self):
        latest = datetime.datetime.now() - self.maxage

        with self.rlock:
            to_clear = [
                key
                for key, (d, val) in self.pool.items()
                if d < latest
            ]
            for k in to_clear:
                del self.pool[k]

    def __delitem__(self, key):
        with self.rlock:
            del self.pool[key]

    def __getitem__(self, key):
        with self.rlock:
            return self.pool[key][1]

    def get(self, key, default=None):
        with self.rlock:
            if key in self.pool:
                return self.pool.get(key)[1]
            else:
                return default

    def __setitem__(self, key, value):
        with self.rlock:
            self.pool[key] = (datetime.datetime.now(), value)
        self._clean_cache()


class RestApiStorage(Storage):
    def __init__(self):
        self.result_file_pool = ExpirableDict()

    def prepare_result_from_api(self, result, cursor):
        # result is the full url from the api, we will return only the name,
        # and store the full url for later
        name = os.path.basename(result)
        self.result_file_pool[name] = result, cursor
        return name

    def _open(self, name, mode='rb'):
        if 'r' not in mode:
            NotImplementedError("This backend doesn't support writing on file.")
        cursor = self.get_cursor(name)  # fetch a valid cursor which just got the name
        response = cursor.session.get(self.url(name), stream=True)
        return File(response.raw.file_to_stream, name)

    def _save(self, name, content):
        # self.uploaded_file_pool[id] = content
        content.original_name = name
        return content

    def get_cursor(self, name):
        return self.result_file_pool[name][1]  # pool contains url and cursor to get it

    def url(self, name):
        """return a usable url fro this name"""
        # since the api return us a full url, and it's concidered just the name by django
        # we don't do anything

        return self.result_file_pool.get(name, (name, None))[0]  # pool contains url and cursor to get it

    def get_available_name(self, name, max_length=None):
        return name
