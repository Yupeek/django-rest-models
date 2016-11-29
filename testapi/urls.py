# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.conf.urls import include, url
from django.contrib import admin
from django.http.response import HttpResponseForbidden
from django.views.generic.base import RedirectView
from dynamic_rest.routers import DynamicRouter

from testapi.viewset import AuthorizedPizzaViewSet, MenuViewSet, PizzaViewSet, ToppingViewSet, wait

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
