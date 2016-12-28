# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import datetime
import logging

from django.conf import settings
from django.db import models
from django.utils import timezone

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

    def __str__(self):
        return self.name  # pragma: no cover


class Pizza(models.Model):

    name = models.CharField(max_length=125)
    price = models.FloatField()
    from_date = models.DateField(auto_now_add=True)
    to_date = models.DateTimeField(default=auto_now_plus_5d)

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    toppings = models.ManyToManyField(Topping, related_name='pizzas')
    menu = models.ForeignKey(Menu, null=True, related_name='pizzas')

    def __str__(self):
        return self.name  # pragma: no cover
