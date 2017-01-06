# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from dynamic_rest.fields.fields import DynamicRelationField
from dynamic_rest.serializers import DynamicModelSerializer

from testapi.badapi.models import AA, BB, A, B


class ASerializer(DynamicModelSerializer):
    class Meta:
        model = A
        name = 'a'
        fields = ('id', 'name')


class BSerializer(DynamicModelSerializer):
    class Meta:
        model = B
        name = 'b'
        fields = ('id', 'name')


class AASerializer(DynamicModelSerializer):
    a = DynamicRelationField(ASerializer, many=False)

    class Meta:
        model = AA
        name = 'aa'
        fields = ('id', 'name', 'a')


class BBSerializer(DynamicModelSerializer):
    b = DynamicRelationField(BSerializer, many=True)

    class Meta:
        model = BB
        name = 'bb'
        fields = ('id', 'name', 'b')
