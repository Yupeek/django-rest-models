# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import datetime
import logging

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def auto_now_plus_5d():
    return timezone.now() + datetime.timedelta(days=5)


class A(models.Model):
    name = models.CharField(max_length=135)

    class APIMeta:
        db_name = 'apifail'


class B(models.Model):
    name = models.CharField(max_length=135)

    class APIMeta:
        db_name = 'apifail'


class C(models.Model):
    name = models.CharField(max_length=135)

    class APIMeta:
        db_name = 'apifail'


class AA(models.Model):
    name = models.CharField(max_length=135)
    a = models.ForeignKey(A, related_name='aa')

    class APIMeta:
        db_name = 'apifail'


class BB(models.Model):
    name = models.CharField(max_length=135)
    b = models.ManyToManyField(B, related_name='bb')
    a = models.ManyToManyField(A, related_name='bb')

    class APIMeta:
        db_name = 'apifail'
