#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, absolute_import
from django.db import models


class ModelA(models.Model):
    pass


class ModelB(models.Model):
    a = models.ForeignKey(ModelA)

