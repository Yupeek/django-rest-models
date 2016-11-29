# -*- coding: utf-8 -*-


from django.contrib import admin

from testapi.models import Menu, Pizza, Topping

admin.site.register([Pizza, Topping, Menu])
