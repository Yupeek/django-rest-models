==================
django-rest-models
==================

Allow to query a **django** RestAPI with same interface as the django ORM. **(the targeted API must use django-rest-framework + dynamic-rest libraries)**
In fact, it works like any other database engine. You add the rest_models engine in an alternate database and the rest_models databe router.
Then add APIMeta class to the models querying the API, voilà !

Stable branch

.. image:: https://img.shields.io/travis/Yupeek/django-rest-models/master.svg
    :target: https://travis-ci.org/Yupeek/django-rest-models

.. image:: https://readthedocs.org/projects/django-rest-models/badge/?version=latest
    :target: http://django-rest-models.readthedocs.org/en/latest/

.. image:: https://coveralls.io/repos/github/Yupeek/django-rest-models/badge.svg?branch=master
    :target: https://coveralls.io/github/Yupeek/django-rest-models?branch=master

.. image:: https://img.shields.io/pypi/v/django-rest-models.svg
    :target: https://pypi.python.org/pypi/django-rest-models
    :alt: Latest PyPI version

.. image:: https://requires.io/github/Yupeek/django-rest-models/requirements.svg?branch=master
     :target: https://requires.io/github/Yupeek/django-rest-models/requirements/?branch=master
     :alt: Requirements Status

Development status

.. image:: https://img.shields.io/travis/Yupeek/django-rest-models/develop.svg
    :target: https://travis-ci.org/Yupeek/django-rest-models

.. image:: https://coveralls.io/repos/github/Yupeek/django-rest-models/badge.svg?branch=develop
    :target: https://coveralls.io/github/Yupeek/django-rest-models?branch=develop

.. image:: https://requires.io/github/Yupeek/django-rest-models/requirements.svg?branch=develop
     :target: https://requires.io/github/Yupeek/django-rest-models/requirements/?branch=develop
     :alt: Requirements Status


Installation
------------

1. Install using pip:

   ``pip install django-rest-models``

2. Alternatively, you can download or clone this repo and install with :

    ``pip install -e .``.

Requirements
------------

This database wrapper work with

- python 3.6, 3.7
- django 2.0, 2.1, 2.2

On the api, this is tested against

- django-rest-framework 3.11, 3.12, 3.13
- dynamic-rest 2.1


Examples
--------

settings.py:

.. code-block:: python

    DATABASES = {
        'default': {
            ...
        },
        'api': {
            'ENGINE': 'rest_models.backend',
            'NAME': 'https://requestb.in/',
            'USER': 'userapi',
            'PASSWORD': 'passwordapi',
            'AUTH': 'rest_models.backend.auth.BasicAuth',
        },
    }

    DATABASE_ROUTERS = [
        'rest_models.router.RestModelRouter',
    ]


models.py:

.. code-block:: python

    class MyModel(models.Model):
        field = models.IntegerField()
        ...

        class Meta:
            # basic django meta Stuff
            verbose_name = 'my model'

        # the only customisation that make this model special
        class APIMeta:
            pass


    class MyOtherModel(models.Model):
        other_field = models.IntegerField()
        first_model = models.ForeignKey(MyModel, db_column='mymodel')
        ...

        class Meta:
            # basic django meta Stuff
            verbose_name = 'my other model'

        # the only customisation that make this model special
        class APIMeta:
            pass



Targeted API requirements
-------------------------

To allow this database adapter to work like a relational one, the targeted API must respect some requirements :

- dynamic-rest installed and all serializers/views must respectively inherit from Dynamic* (DynamicModelSerializer, etc...)

Each API serializer must :

- Provide the id field
- Provide the related field (ManyToMany and ForeignKey on Models) as DynamicRelationField
- Provide the reverse related field. We must, for each ForeignKey and ManyToMany, add a field on the related model's
  serializer.

.. code-block:: python

    class MenuSerializer(DynamicModelSerializer):
        pizzas = DynamicRelationField('PizzaSerializer', many=True)     # Menu.pizza = ManyToMany

        class Meta:
            model = Menu
            name = 'menu'
            fields = ('id', 'code', 'name', 'pizzas')
            deferred_fields = ('pizza_set', )


    class PizzaSerializer(DynamicModelSerializer):

        toppings = DynamicRelationField(ToppingSerializer, many=True)
        menu = DynamicRelationField(MenuSerializer)                     # Add this because Menu.pizza = ManyToMany

        class Meta:
            model = Pizza
            name = 'pizza'
            fields = ('id', 'name', 'price', 'from_date', 'to_date', 'toppings', 'menu')

django-rest-models provide a way to check the consistency of the api with the local models via the django check framework.
At each startup, it will query the api with OPTIONS to check if the local models match the remote serializers.


Caveats
-------

Since this is not a real relational database, all feature cannot be implemented. Some limitations are inherited by
dynamic-rest filtering system too.

- Aggregations : is not implemented on the api endpoint, maybe in future releases
- Complex filtering using OR : all filter passed to dynamic-rest is ANDed together, so no OR is possible
- Negated AND in filtering: a negated AND give a OR, so previous limitation apply
- Negated OR in filtering: since the compitation of nested filter is complexe and error prone, we disable all OR. in
  fact, only some nested of AND is accepted. only the final value of the Q() object can be negated

    for short, you **CANNOT** :

.. code-block:: python


        Pizza.objects.aggregate()
        Pizza.objects.annotate()
        Pizza.objects.filter(Q(..) | Q(..))
        Pizza.objects.exclude(Q(..) & Q(..))
        Pizza.objects.exclude(Q(..) | Q(..))

    but you can :

.. code-block:: python

        Pizza.objects.create
        Pizza.objects.bulk_create
        Pizza.objects.update
        Pizza.objects.bulk_update
        Pizza.objects.select_related
        Pizza.objects.prefetch_related
        Pizza.objects.values
        Pizza.objects.values_list
        Pizza.objects.delete
        Pizza.objects.count()
        Pizza.objects.filter(..., ..., ...)
        Pizza.objects.filter(...).filter(...).exclude(...)
        Pizza.objects.exclude(..., ...).exclude(...)
        Pizza.objects.filter(Q(..) & Q(..))
        Pizza.objects.none()
        pizza.toppings.add(...)
        pizza.toppings.remove(...)
        pizza.toppings.set(...)
        pizza.toppings.clear(...)

.. note::

    prefetch_related work as expected, but the performance is readly bad. As a matter of fact, a ``Pizza.objects.prefetch_related('toppings')``
    will query the toppings for all pizzas as expected, but the query to recover the pizza will contains the linked pizza in the response.
    If the database contains a great number of pizzas for the given toppings, the response will contains them all, even if it's
    useless at first glance, the linked pizza for each topping is mandotary to django to glue topping <=> pizza relationships.

    So, be careful when using prefetch_related.



Specific behaviour
---------------------

Some specific behaviour has been implemented to use the extra feature of a Rest API :

- When inserting, the resulting model is returned by the API. the inserted model is updated with the resulting values.
  This imply 2 things:

  * If you provided default values for fields in the api, these data will be populated into your created instance if it was ommited.
  * If the serializer have some computed data, its data will always be used as a replacement of the one you gave to your
    models. (cf example: Pizza.cost which is the sum of the cost of the toppling. after each save, its value will be updated)


Support
-------

This database api support :

- select_related
- order_by
- only
- defer
- filter
- exclude
- delete
- update
- create
- bulk create (with retrive of pk)
- ManyToManyField
- ForeignKey*

.. note::

    ForeignKey must have db_column fixed to the name of the reflected field in the api. or all update/create won't use
    the value if this field

.. note::

		Support for ForeignKey is only available with models on the same database (api<->api) or (default<->default).
		It's not possible to add a ForeignKey/ManyToMany field on a local model related to a remote model (with ApiMeta)

Documentation
-------------

The full documentation is at http://django-rest-models.readthedocs.org/en/latest/.


Requirements
------------

- Python 2.7, 3.5
- Django >= 1.8

Contributions and pull requests are welcome.


Bugs and requests
-----------------

If you found a bug or if you have a request for additional feature, please use the issue tracker on GitHub.

https://github.com/Yupeek/django-rest-models/issues

known limitations
-----------------

JSONField from postgresql and mysql is supported by django-rest-models, but not by the current dynamic-rest (1.8.1)
so you can do `MyModel.objects.filter(myjson__mydata__contains='aaa')` but it will work if drest support it

same for DateField's year,month,day lookup.

License
-------

You can use this under GPLv3.

Author
------

Original author: `Darius BERNARD <https://github.com/ornoone>`_.
Contributor: `PaulWay <https://github.com/PaulWay>`_.


Thanks
------

Thanks to django for this amazing framework.
