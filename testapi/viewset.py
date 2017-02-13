# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import time

from django.http.response import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.permissions import DjangoModelPermissions

from testapi.models import Menu, Pizza, PizzaGroup, Topping
from testapi.serializers import MenuSerializer, PizzaGroupSerializer, PizzaSerializer, ToppingSerializer


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


class PizzaGroupViewSet(DynamicModelViewSet):
    serializer_class = PizzaGroupSerializer
    queryset = PizzaGroup.objects.all()


def wait(request):
    time.sleep(0.5)
    return HttpResponse()


queries = []
""":type: list[django.core.handlers.wsgi.WSGIRequest] """
custom = {}


@csrf_exempt
def fake_oauth(request):
    queries.append(request)
    res = {"access_token": "zU9inLFU8UmIJe6hnkGT9KXtcWwPFY", "token_type": "Bearer", "expires_in": 36000,
           "scope": "read write"}
    res.update(custom)
    return JsonResponse(res, status=custom.get('status_code', 200))


@csrf_exempt
def fake_view(request):
    queries.append(request)
    return HttpResponse('hello world')
