# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

from django.db.models.aggregates import Sum
from dynamic_rest.fields.fields import DynamicRelationField
from dynamic_rest.serializers import DynamicModelSerializer
from rest_framework.fields import SerializerMethodField

from testapi.models import Pizza, Topping


class ToppingSerializer(DynamicModelSerializer):
    class Meta:
        model = Topping
        name = 'topping'
        fields = ('name', 'cost')


class PizzaSerializer(DynamicModelSerializer):
    cost = SerializerMethodField()

    toppings = DynamicRelationField(ToppingSerializer, many=True)

    class Meta:
        model = Pizza
        name = 'pizza'
        fields = ('id', 'name', 'price', 'from_date', 'to_date', 'cost', 'toppings')

    def get_cost(self, obj):
        return obj.toppings.aggregate(cost=Sum('cost'))['cost']
