# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import datetime
import logging

from django.conf import settings
from django.contrib.gis.db.models import PointField
from django.db import models
from django.db.models import CASCADE
from django.utils import timezone

POSTGIS = False
if settings.DATABASES['default']['ENGINE'] == 'django.contrib.gis.db.backends.postgis':
    class Restaurant(models.Model):
        name = models.CharField(max_length=135)
        location = PointField(
            null=True,
            blank=True,
        )

        def __str__(self):
            return self.name  # pragma: no cover

    POSTGIS = True

if settings.DATABASES['default']['ENGINE'] in ['django.db.backends.postgresql',
                                               'django.contrib.gis.db.backends.postgis']:
    from django.contrib.postgres.fields import JSONField

    has_jsonfield = True
else:
    # fake useless jsonfield
    def JSONField(*args, **kwargs):
        return None

    has_jsonfield = False

logger = logging.getLogger(__name__)


def auto_now_plus_5d():
    return timezone.now() + datetime.timedelta(days=5)


class Menu(models.Model):
    name = models.CharField(max_length=135)
    code = models.CharField(max_length=3)

    def __str__(self):
        return self.name  # pragma: no cover


class Topping(models.Model):
    name = models.CharField(max_length=125)
    cost = models.FloatField()
    metadata = JSONField(null=True)

    def __str__(self):
        return self.name  # pragma: no cover


class Pizza(models.Model):
    name = models.CharField(max_length=125)
    price = models.FloatField()
    from_date = models.DateField(auto_now_add=True)
    to_date = models.DateTimeField(default=auto_now_plus_5d)

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=CASCADE)
    toppings = models.ManyToManyField(Topping, related_name='pizzas', blank=True)
    menu = models.ForeignKey(Menu, null=True, related_name='pizzas', on_delete=CASCADE)

    def __str__(self):
        return self.name  # pragma: no cover


class Review(models.Model):
    comment = models.TextField(blank=True)
    photo = models.ImageField(null=True)

    def __str__(self):
        return "review %s" % self.id  # pragma: no cover


class PizzaGroup(models.Model):
    parent = models.ForeignKey("self", related_name='children', null=True, on_delete=CASCADE)
    name = models.CharField(max_length=125)
    pizzas = models.ManyToManyField(Pizza, related_name='groups')

    def __str__(self):
        return self.name
