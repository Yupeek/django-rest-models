# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

from dynamic_rest.viewsets import DynamicModelViewSet

from testapi.models import Pizza, Topping
from testapi.serializers import PizzaSerializer, ToppingSerializer


class PizzaViewSet(DynamicModelViewSet):
    queryset = Pizza.objects.all()
    serializer_class = PizzaSerializer


class ToppingViewSet(DynamicModelViewSet):
    queryset = Topping.objects.all()
    serializer_class = ToppingSerializer

