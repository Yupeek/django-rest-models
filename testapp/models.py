#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, absolute_import
from django.db import models


class ModelA(models.Model):

    def __str__(self):
        return "A[%d]" % self.pk

    class APIMeta:
        pass


class ModelB(models.Model):
    a = models.ForeignKey(ModelA)

    def __str__(self):
        return "B[%d](%s)" % (self.pk, self.a)

    class APIMeta:
        pass
