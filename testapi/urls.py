# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

from django.conf.urls import patterns, url, include
from dynamic_rest.routers import DynamicRouter
from django.contrib import admin

from testapi.viewset import PizzaViewSet, ToppingViewSet, AuthorizedPizzaViewSet, wait

router = DynamicRouter()
router.register('/pizza', PizzaViewSet)
router.register('/topping', ToppingViewSet)

router.register('/authpizza', AuthorizedPizzaViewSet)

urlpatterns = [
    url(r'^api/v2/wait', wait),
    url(r'^api/v2', include(router.urls)),
    url(r'admin/', include(admin.site.urls))
]
