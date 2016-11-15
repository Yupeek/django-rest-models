# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

from django.conf.urls import patterns, url, include
from dynamic_rest.routers import DynamicRouter

from testapi.viewset import PizzaViewSet, ToppingViewSet

router = DynamicRouter()

router.register('/pizza', PizzaViewSet)
router.register('/topping', ToppingViewSet)

urlpatterns = patterns('',
    url(r'^api/v2', include(router.urls))
)
