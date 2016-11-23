#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, absolute_import

from django.conf import settings
from django.db import models


class ModelA(models.Model):
    name = models.CharField(max_length=135)

    class APIMeta:
        pass

