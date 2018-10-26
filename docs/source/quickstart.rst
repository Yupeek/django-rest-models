Quick start
###########


Client
******



Settings
========

- add the router ``'rest_models.router.RestModelRouter'`` to the setting ``DATABASE_ROUTERS``
- add your api to the ``DATABASES`` setting


.. code-block:: python

    DATABASES = {
        'default': {
            ...
        },
        'api': {
            'ENGINE': 'rest_models.backend',
            'NAME': 'http://127.0.0.1:8001/api/v2/',
            'USER': 'interim',
            'PASSWORD': 'interim',
            'AUTH': 'rest_models.backend.auth.OAuthToken',
            'OPTIONS': {
                'OAUTH_URL': '/oauth2/token/',
                'TIMEOUT': 10,
            }
        },
    }

    DATABASE_ROUTERS = [
        'rest_models.router.RestModelRouter',
    ]



Models
======

Create your models that will match your serializers on the api.
The only customisation to make it a non database model is the addition of the class ``APIMeta``.
Thanks to the RestModelRouter, this addition will choose the database with the rest_models backend
as the backend to use.

.. code-block:: python

    class MyModel(models.Model):
        field = models.IntegerField()
        ...

        class Meta:
            # basic django meta Stuff
            verbose_name = 'my model'

        # the only customisation that makes this model special
        class APIMeta:
            pass

Usage
=====

Use it as any normal Django Model. Just keep in mind that the backend is not a SGDB and it may not be
performant on all queryset, and that some query is not possible.

You can not:

- aggregate
- annotate
- make complex filters with NOT and OR

API side
********

On the API side, you don't need to install this lib. But the serializers must follow these constraint :

- inherit the ``DynamicModelSerializer`` from ``dynamic-rest``
- provide all related serializers using ``DynamicRelationField`` from ``dynamic-rest``
- provide all backward relation in both serializers.


Examples
========

with the folowing models

.. code-block:: python

    class Menu(models.Model):
        name = models.CharField(max_length=135)
        code = models.CharField(max_length=3)

        def __str__(self):
            return self.name  # pragma: no cover


    class Topping(models.Model):
        name = models.CharField(max_length=125)
        cost = models.FloatField()

        def __str__(self):
            return self.name  # pragma: no cover


    class Pizza(models.Model):

        name = models.CharField(max_length=125)
        price = models.FloatField()
        from_date = models.DateField(auto_now_add=True)
        to_date = models.DateTimeField(default=auto_now_plus_5d)

        creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
        toppings = models.ManyToManyField(Topping, related_name='pizzas')
        menu = models.ForeignKey(Menu, null=True, related_name='pizzas')

        def __str__(self):
            return self.name  # pragma: no cover





Inheritance
===========

* inherit the ``DynamicModelSerializer`` from ``dynamic-rest``

Bad::

    from rest_framework import serializers

    class MenuSerializer(serializers.Serializer):
        ...


Good::

    from dynamic_rest.serializers import DynamicModelSerializer

    class MenuSerializer(DynamicModelSerializer):
        ...

Related serializers fields
==========================

* Provide all related serializers using ``DynamicRelationField`` from ``dynamic-rest``

Bad::


    class PizzaSerializer(DynamicModelSerializer):
        toppings = ToppingSerializer(many=True)

Good::

    from dynamic_rest.fields.fields import DynamicRelationField

    class PizzaSerializer(DynamicModelSerializer):
        toppings = DynamicRelationField(ToppingSerializer, many=True)

Backward relationship
=====================

* Provide all backward relation in both serializers.

bad::


    class MenuSerializer(DynamicModelSerializer):
        # missing backward serializer to pizza, which have a «menu» foreignkey

        class Meta:
            model = Menu
            name = 'menu'
            fields = ('id', 'code', 'name')


    class PizzaSerializer(DynamicModelSerializer):

        menu = DynamicRelationField(MenuSerializer)

        class Meta:
            model = Pizza
            name = 'pizza'
            fields = ('id', 'name', 'price', 'from_date', 'to_date', 'menu')


Good::

    class MenuSerializer(DynamicModelSerializer):
        pizzas = DynamicRelationField('PizzaSerializer', many=True)  # good backward link. respecting menu.related_name

        class Meta:
            model = Menu
            name = 'menu'
            fields = ('id', 'code', 'name', 'pizzas')


    class PizzaSerializer(DynamicModelSerializer):

        menu = DynamicRelationField(MenuSerializer)

        class Meta:
            model = Pizza
            name = 'pizza'
            fields = ('id', 'name', 'price', 'from_date', 'to_date', 'menu')

