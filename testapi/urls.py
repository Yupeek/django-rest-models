# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import django.views.static
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.http.response import HttpResponse, HttpResponseForbidden
from django.views.generic.base import RedirectView
from dynamic_rest.routers import DynamicRouter

from testapi.viewset import (AuthorizedPizzaViewSet, MenuViewSet, PizzaGroupViewSet, PizzaViewSet, ReviewViewSet,
                             ToppingViewSet, fake_oauth, fake_view, wait)

router = DynamicRouter()
router.register('pizza', PizzaViewSet, base_name='pizza')
router.register('review', ReviewViewSet)
router.register('topping', ToppingViewSet)
router.register('menulol', MenuViewSet)
router.register('pizzagroup', PizzaGroupViewSet)

router.register('authpizza', AuthorizedPizzaViewSet)

urlpatterns = [
    url(r'^api/v2/wait', wait),
    url(r'^oauth2/token/$', fake_oauth),
    url(r'^api/v2/view/$', fake_view),
    url(r'^api/v2/', include(router.urls)),
    url(r'^api/forbidden', lambda request: HttpResponseForbidden()),
    url(r'^other/view/', lambda request: HttpResponse(b'{"result": "ok"}')),
    url(r'admin/', include(admin.site.urls)),
    url(r'^$', RedirectView.as_view(url='api/v2', permanent=False))
]
# static files (images, css, javascript, etc.)
urlpatterns += [
    url(r'^media/(?P<path>.*)$', django.views.static.serve, {'document_root': settings.MEDIA_ROOT})
]
