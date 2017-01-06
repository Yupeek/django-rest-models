# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from dynamic_rest.viewsets import DynamicModelViewSet

from .models import AA, BB, A, B
from .serializers import AASerializer, ASerializer, BBSerializer, BSerializer


class AViewSet(DynamicModelViewSet):
    serializer_class = ASerializer
    queryset = A.objects.all()


class AAViewSet(DynamicModelViewSet):
    serializer_class = AASerializer
    queryset = AA.objects.all()


class BViewSet(DynamicModelViewSet):
    serializer_class = BSerializer
    queryset = B.objects.all()


class BBViewSet(DynamicModelViewSet):
    serializer_class = BBSerializer
    queryset = BB.objects.all()
