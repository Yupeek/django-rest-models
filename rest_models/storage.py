# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging
import os
import threading

import unidecode
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.http import urlunquote

from rest_models.backend.connexion import get_basic_session

logger = logging.getLogger(__name__)


class ExpirableDict(dict):

    def __init__(self, maxage=datetime.timedelta(hours=1)):
        self.maxage = maxage
        self.rlock = threading.RLock()
        super(ExpirableDict, self).__init__()

    def _clean_cache(self):
        latest = datetime.datetime.now() - self.maxage

        with self.rlock:
            to_clear = [
                key
                for key, (d, val) in self.items()
                if d < latest
            ]
            for k in to_clear:
                del self[k]

    def __delitem__(self, key):
        with self.rlock:
            super(ExpirableDict, self).__delitem__(key)

    def __getitem__(self, key):
        with self.rlock:
            return super(ExpirableDict, self).__getitem__(key)[1]

    def get(self, key, default=None):
        with self.rlock:
            if key in self:
                return super(ExpirableDict, self).get(key)[1]
            else:
                return default

    def pop(self, key, default=None):
        with self.rlock:
            return super(ExpirableDict, self).pop(key, default)

    def __setitem__(self, key, value):
        with self.rlock:
            super(ExpirableDict, self).__setitem__(key, (datetime.datetime.now(), value))
        self._clean_cache()


@deconstructible
class RestApiStorage(Storage):
    def __init__(self):
        self.result_file_pool = ExpirableDict()

    def prepare_result_from_api(self, result, cursor):
        # result is the full url from the api, we will return only the name,
        # and store the full url for later
        if result is None:
            return None
        name = urlunquote(os.path.basename(result))
        self.result_file_pool[name] = result, cursor
        return name

    def _open(self, name, mode='rb'):
        if 'r' not in mode:
            NotImplementedError("This backend doesn't support writing on file.")
        cursor = self.get_cursor(name)  # fetch a valid cursor which just got the name
        url = self.url(name)
        # try with anonymous data
        response = get_basic_session().get(url)
        # if we fail, we try with authenticated session
        if response.status_code in (403, 401):
            response = cursor.session.get(url)
        response.raise_for_status()
        return ContentFile(response.content, name)

    def _save(self, name, content):
        # self.uploaded_file_pool[id] = content
        content.name = content.original_name = name
        return content

    def size(self, name):
        cursor = self.get_cursor(name)  # fetch a valid cursor which just got the name
        url = self.url(name)
        # try with anonymous data
        response = get_basic_session().get(url, stream=True)
        # if we fail, we try with authenticated session
        if response.status_code in (403, 401):
            response = cursor.session.get(url, stream=True)

        return response.headers['Content-length']

    def get_cursor(self, name):
        return self.result_file_pool[name][1]  # pool contains url and cursor to get it

    def url(self, name):
        """return a usable url fro this name"""
        # since the api return us a full url, and it's concidered just the name by django
        # we don't do anything

        return self.result_file_pool.get(name, (name, None))[0]  # pool contains url and cursor to get it

    def get_available_name(self, name, max_length=None):
        return unidecode.unidecode(name)

    def get_valid_name(self, name):
        return unidecode.unidecode(name)
