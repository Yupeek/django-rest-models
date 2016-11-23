# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

from django.conf.urls import url, include
from django.http.response import HttpResponseForbidden
from django.views.generic.base import RedirectView
from dynamic_rest.routers import DynamicRouter
from django.contrib import admin

from testapi.viewset import PizzaViewSet, ToppingViewSet, AuthorizedPizzaViewSet, wait, MenuViewSet

router = DynamicRouter()
router.register('/pizza', PizzaViewSet)
router.register('/topping', ToppingViewSet)
router.register('/menulol', MenuViewSet)

router.register('/authpizza', AuthorizedPizzaViewSet)

urlpatterns = [
    url(r'^api/v2/wait', wait),
    url(r'^api/v2', include(router.urls)),
    url(r'^api/forbidden', lambda request: HttpResponseForbidden()),
    url(r'admin/', include(admin.site.urls)),
    url(r'^$', RedirectView.as_view(url='api/v2', permanent=False))
]
