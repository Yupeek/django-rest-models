# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.urls import include, path
from dynamic_rest.routers import DynamicRouter

from .viewset import AAViewSet, AViewSet, BBViewSet, BViewSet

router = DynamicRouter()
router.register('a', AViewSet)
router.register('aa', AAViewSet)
router.register('b', BViewSet)

router.register('bb', BBViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('', include('testapi.urls')),
]
