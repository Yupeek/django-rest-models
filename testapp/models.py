#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.db import models


class Menu(models.Model):
    name = models.CharField(max_length=135)
    code = models.CharField(max_length=3)

    class APIMeta:
        db_name = 'api'
        ressource_path = 'menulol/'


class Topping(models.Model):
    name = models.CharField(max_length=125)
    cost = models.FloatField()

    class APIMeta:
        db_name = 'api'


class Pizza(models.Model):

    name = models.CharField(max_length=125)
    price = models.FloatField()
    from_date = models.DateField(auto_now_add=True)
    to_date = models.DateTimeField()

    # creator is removed from here but is in the serializer

    # creator = models.ForeignKey(settings.AUTH_USER_MODEL)
    toppings = models.ManyToManyField(Topping, related_name='pizzas')
    menu = models.ForeignKey(Menu, null=True, related_name='pizzas')

    # extra field from serializers
    cost = models.FloatField()

    class APIMeta:
        db_name = 'api'


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    pizza = models.ForeignKey(Pizza)
    date = models.DateTimeField(auto_now_add=True)
