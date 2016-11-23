#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import, print_function, unicode_literals

from django.db import models


class ModelA(models.Model):
    name = models.CharField(max_length=135)

    class APIMeta:
        pass
