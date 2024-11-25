# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import django.views.static
from django.conf import settings
from django.contrib import admin
from django.http.response import HttpResponse, HttpResponseForbidden
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from dynamic_rest.routers import DynamicRouter

from testapi.viewset import (POSTGIS, AuthorizedPizzaViewSet, MenuViewSet, PizzaGroupViewSet, PizzaViewSet,
                             ReviewViewSet, ToppingViewSet, fake_oauth, fake_view, wait)

router = DynamicRouter()

if POSTGIS:
    from testapi.viewset import RestaurantViewSet

    router.register('restaurant', RestaurantViewSet)


router.register('pizza', PizzaViewSet)
router.register('review', ReviewViewSet)
router.register('topping', ToppingViewSet)
router.register('menulol', MenuViewSet)
router.register('pizzagroup', PizzaGroupViewSet)
router.register('authpizza', AuthorizedPizzaViewSet)

urlpatterns = [
    re_path(r'^api/v2/wait', wait),
    path('oauth2/token/', fake_oauth),
    path('api/v2/view/', fake_view),
    path('api/v2/', include(router.urls)),
    re_path(r'^api/forbidden', lambda request: HttpResponseForbidden()),
    re_path(r'^other/view/', lambda request: HttpResponse(b'{"result": "ok"}')),
    re_path(r'admin/', admin.site.urls),
    path('', RedirectView.as_view(url='api/v2', permanent=False))
]
# static files (images, css, javascript, etc.)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', django.views.static.serve, {'document_root': settings.MEDIA_ROOT})
]
