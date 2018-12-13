#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.db import models

from rest_models.storage import RestApiStorage

if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    from rest_models.backend.utils import JSONField
    has_jsonfield = True
else:
    # fake useless jsonfield
    def JSONField(*args, **kwargs):
        return None
    has_jsonfield = False


class Menu(models.Model):
    name = models.CharField(max_length=135)
    code = models.CharField(max_length=3)

    class APIMeta:
        db_name = 'api'
        resource_path = 'menulol'


class Topping(models.Model):
    name = models.CharField(max_length=125)
    cost = models.FloatField(db_column='taxed_cost')
    metadata = JSONField(null=True)

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
    menu = models.ForeignKey(Menu, null=True, related_name='pizzas', db_column='menu')

    # extra field from serializers
    cost = models.FloatField()

    class APIMeta:
        db_name = 'api'


class Review(models.Model):
    comment = models.TextField(blank=True)
    photo = models.ImageField(null=True, storage=RestApiStorage())

    class APIMeta:
        db_name = 'api'


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    pizza_id = models.IntegerField(null=False)
    date = models.DateTimeField(auto_now_add=True)

    @property
    def pizza(self):
        return Pizza.objects.get(pk=self.pizza_id)

    @pizza.setter
    def pizza(self, pizza):
        self.pizza_id = pizza.pk


class PizzaGroup(models.Model):

    parent = models.ForeignKey("self", related_name='children', db_column='parent')
    name = models.CharField(max_length=125)
    pizzas = models.ManyToManyField(Pizza, related_name='groups')

    def __str__(self):
        return self.name

    class APIMeta:
        db_name = 'api'
