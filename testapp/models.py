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
        resource_path = 'menulol'


class Topping(models.Model):
    name = models.CharField(max_length=125)
    cost = models.FloatField(db_column='taxed_cost')

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


class Pizza_topping(models.Model):
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE, db_column='pizza', related_name='+')
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE, db_column='topping', related_name='+')

    class APIMeta:
        db_name = 'api'

        resource_name = 'Pizza_topping'
        resource_name_plural = 'Pizza_toppings'

    class Meta:
        auto_created = True


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    pizza = models.ForeignKey(Pizza)
    date = models.DateTimeField(auto_now_add=True)


class PizzaGroup(models.Model):

    parent = models.ForeignKey("self", related_name='children', db_column='parent')
    name = models.CharField(max_length=125)
    pizzas = models.ManyToManyField(Pizza, related_name='groups')

    def __str__(self):
        return self.name

    class APIMeta:
        db_name = 'api'
