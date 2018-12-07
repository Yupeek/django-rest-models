# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db.models.aggregates import Sum
from dynamic_rest.fields.fields import DynamicRelationField
from dynamic_rest.serializers import DynamicModelSerializer
from rest_framework.fields import IntegerField, SerializerMethodField

from testapi.models import Menu, Pizza, PizzaGroup, Review, Topping


class ToppingSerializer(DynamicModelSerializer):
    class Meta:
        model = Topping
        name = 'topping'
        fields = ('id', 'name', 'taxed_cost', 'pizzas',) + (('metadata', ) if Topping.metadata else ())
        defered_fields = ('pizzas',)

    pizzas = DynamicRelationField('PizzaSerializer', many=True, required=False)

    taxed_cost = IntegerField(source='cost')


class MenuSerializer(DynamicModelSerializer):
    pizzas = DynamicRelationField('PizzaSerializer', many=True, required=False)

    class Meta:
        model = Menu
        name = 'menu'
        fields = ('id', 'code', 'name', 'pizzas')
        deferred_fields = ('pizza_set', )


class PizzaSerializer(DynamicModelSerializer):
    cost = SerializerMethodField()

    toppings = DynamicRelationField(ToppingSerializer, many=True, required=False)
    groups = DynamicRelationField('PizzaGroupSerializer', many=True, required=False)
    menu = DynamicRelationField(MenuSerializer, many=False, required=False)

    class Meta:
        model = Pizza
        name = 'pizza'
        fields = ('id', 'name', 'price', 'from_date', 'to_date', 'cost', 'toppings', 'menu', 'groups',)
        defered_fields = ('toppings', 'groups', 'menu',)

    def get_cost(self, obj):
        return obj.toppings.aggregate(cost=Sum('cost'))['cost']


class ReviewSerializer(DynamicModelSerializer):

    class Meta:
        model = Review
        name = 'review'
        fields = ('id', 'comment', 'photo', )


class PizzaGroupSerializer(DynamicModelSerializer):

    pizzas = DynamicRelationField(PizzaSerializer, many=True)

    children = DynamicRelationField('PizzaGroupSerializer', many=True)
    parent = DynamicRelationField('PizzaGroupSerializer', many=False)

    class Meta:
        model = PizzaGroup
        name = 'pizzagroup'
        fields = ('id', 'name', 'pizzas', 'children', 'parent')


# many2many through serializer
class PizzaToppingsSerializer(DynamicModelSerializer):
    class Meta:
        model = Pizza._meta.get_field('toppings').rel.through
        name = 'Pizza_topping'
        fields = ('id', 'pizza', 'topping',)

    topping = DynamicRelationField('ToppingSerializer', many=False, required=False)
    pizza = DynamicRelationField('PizzaSerializer', many=False, required=False)
