# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db.models.aggregates import Sum
from dynamic_rest.fields.fields import DynamicRelationField
from dynamic_rest.serializers import DynamicModelSerializer
from rest_framework.fields import SerializerMethodField

from testapi.models import Menu, Pizza, PizzaGroup, Topping


class ToppingSerializer(DynamicModelSerializer):
    class Meta:
        model = Topping
        name = 'topping'
        fields = ('id', 'name', 'cost', 'pizzas')


class MenuSerializer(DynamicModelSerializer):
    pizzas = DynamicRelationField('PizzaSerializer', many=True)

    class Meta:
        model = Menu
        name = 'menu'
        fields = ('id', 'code', 'name', 'pizzas')
        deferred_fields = ('pizza_set', )


class PizzaSerializer(DynamicModelSerializer):
    cost = SerializerMethodField()

    toppings = DynamicRelationField(ToppingSerializer, many=True)
    groups = DynamicRelationField('PizzaGroupSerializer', many=True)
    menu = DynamicRelationField(MenuSerializer)

    class Meta:
        model = Pizza
        name = 'pizza'
        fields = ('id', 'name', 'price', 'from_date', 'to_date', 'cost', 'toppings', 'menu', 'groups')

    def get_cost(self, obj):
        return obj.toppings.aggregate(cost=Sum('cost'))['cost']


class PizzaGroupSerializer(DynamicModelSerializer):

    pizzas = DynamicRelationField(PizzaSerializer, many=True)

    children = DynamicRelationField('PizzaGroupSerializer', many=True)
    parent = DynamicRelationField('PizzaGroupSerializer', many=False)

    class Meta:
        model = PizzaGroup
        name = 'pizzagroup'
        fields = ('id', 'name', 'pizzas', 'children', 'parent')
