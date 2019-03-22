# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import time

from django.db.models import Q
from django.http.response import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.permissions import DjangoModelPermissions

from testapi.models import Menu, Pizza, PizzaGroup, Review, Topping
from testapi.serializers import (MenuSerializer, PizzaGroupSerializer, PizzaSerializer, ReviewSerializer,
                                 ToppingSerializer)


class OrFilteringMixin(object):
    """
    Mixin to filter queryset with custom or clause sent by django-rest-models
    """
    def filter_queryset(self, queryset):
        qs = super(OrFilteringMixin, self).filter_queryset(queryset)
        or_params = self.extract_or_params()
        if or_params:
            qs = self.filter_with_or(qs, or_params)
        return qs

    def extract_or_params(self):
        or_params = []
        prefix = 'filterOR{'
        offset = len(prefix)
        for name, value in self.request.GET.items():
            if name.startswith(prefix):
                if name.endswith('}'):
                    if '.in' in name:
                        value = self.request.GET.getlist(name)
                    name = name[offset:-1]
                    or_params.append((name, value))
        return or_params

    def filter_with_or(self, qs, or_params):
        queries = None
        for name, value in or_params:
            if '.' in name:
                splitted = name.split('.')
                field = splitted[0]
                lookups = '__'.join(splitted[1:])
                django_param = {'{}__{}'.format(field, lookups): value}
            else:
                django_param = {field: value}
            if queries:
                queries |= Q(**django_param)
            else:
                queries = Q(**django_param)
        return qs.filter(queries)


class PizzaViewSet(OrFilteringMixin, DynamicModelViewSet):
    queryset = Pizza.objects.all()
    serializer_class = PizzaSerializer


class ReviewViewSet(DynamicModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


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
