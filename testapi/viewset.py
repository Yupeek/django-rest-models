# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import time

from django.http.response import HttpResponse
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.permissions import DjangoModelPermissions

from testapi.models import Pizza, Topping, Menu
from testapi.serializers import PizzaSerializer, ToppingSerializer, MenuSerializer


class PizzaViewSet(DynamicModelViewSet):
    queryset = Pizza.objects.all()
    serializer_class = PizzaSerializer


class ToppingViewSet(DynamicModelViewSet):
    queryset = Topping.objects.all()
    serializer_class = ToppingSerializer


class AuthorizedPizzaViewSet(DynamicModelViewSet):
    queryset = Pizza.objects.all()
    serializer_class = PizzaSerializer
    permission_classes = [DjangoModelPermissions]


class MenuViewSet(DynamicModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer


def wait(request):
    time.sleep(0.5)
    return HttpResponse()
