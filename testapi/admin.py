# -*- coding: utf-8 -*-


from django.contrib import admin

from testapi.models import Pizza, Topping, Menu

admin.site.register([Pizza, Topping, Menu])
