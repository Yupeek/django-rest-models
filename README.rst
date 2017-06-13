==================
django-rest-models
==================

allow to query an RestAPI (django-rest-framework + dynamic-rest) with same same interface as the django ORM.
if fact, it work like any other database engin. you add the rest_models engin in an alternate database, the router, and
add a APIMeta class to your models, and let's go.

stable branche

.. image:: https://img.shields.io/travis/Yupeek/django-rest-models/master.svg
    :target: https://travis-ci.org/Yupeek/django-rest-models

.. image:: https://readthedocs.org/projects/django-rest-models/badge/?version=latest
    :target: http://django-rest-models.readthedocs.org/en/latest/

.. image:: https://coveralls.io/repos/github/Yupeek/django-rest-models/badge.svg?branch=master
    :target: https://coveralls.io/github/Yupeek/django-rest-models?branch=master

.. image:: https://img.shields.io/pypi/v/django-rest-models.svg
    :target: https://pypi.python.org/pypi/django-rest-models
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/django-rest-models.svg
    :target: https://pypi.python.org/pypi/django-rest-models
    :alt: Number of PyPI downloads per month

.. image:: https://requires.io/github/Yupeek/django-rest-models/requirements.svg?branch=master
     :target: https://requires.io/github/Yupeek/django-rest-models/requirements/?branch=master
     :alt: Requirements Status

development status

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

2. Alternatively, you can install download or clone this repo and call

    ``pip install -e .``.

requirements
------------

this database wrapper work with

- python 2.7, 3.4, 3.5
- django 1.8 , 1.9, 1.10

on the api, this is tested against

- django-rest-framework 3.4, 3.5
- dynamic-rest 1.5, 1.6


exemples
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
            
   

constraints
-----------

to allow this database adaptater to work like a relational one, the API targeted must respect some requirments

- dynamic-rest installed and all the serializers must provide it's functionnality (hinerit from DynamicModelSerializer)

each serializers must :

- provide the id fields
- provide the related field (ManyToMany and ForeignKey on Models) as DynamicRelationField
- provide the reverse related field (each ForeignKey and manyToMany add a relation on the other models.
  the serializer from the other model must provide the DynamicRelationField for these relation

.. code-block:: python

    class MenuSerializer(DynamicModelSerializer):
        pizzas = DynamicRelationField('PizzaSerializer', many=True)

        class Meta:
            model = Menu
            name = 'menu'
            fields = ('id', 'code', 'name', 'pizzas')
            deferred_fields = ('pizza_set', )


    class PizzaSerializer(DynamicModelSerializer):

        toppings = DynamicRelationField(ToppingSerializer, many=True)
        menu = DynamicRelationField(MenuSerializer)

        class Meta:
            model = Pizza
            name = 'pizza'
            fields = ('id', 'name', 'price', 'from_date', 'to_date', 'toppings', 'menu')

Django rest models provide a way to check the consistency of the api with the local models via the django check framework.
at each startup, it will query the api with OPTIONS to check if the local models match the remote serializers.


limitations
-----------

since this is not a real relational database, all feathure cannot be implemented. some limitations are inherited by
dynamic-rest filtering system too.

- aggregations : is not implemented on the api endpoint. maybe in future release
- complexe filtering using OR : all filter passed to dynamic-rest is ANDed together, so no OR is possible
- negated AND in filtering: a negated AND give a OR, so previous limitation apply
- negated OR in filtering: since the compitation of nested filter is complexe and error prone, we disable all OR. in
  fact, only some nested of AND is accepted. only the final value of the Q() object can be negated

    for short, you can't :

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

.. note::

    prefetch_related work as expected, but the performances is bad. in fact, a ``Pizza.objects.prefetch_related('toppings')``
    will query the toppings for all pizzas as expeced, but the query to recover the pizza will contains the linked pizza in the response.
    if the database contains a great lot of pizza for the given toppings, the response will contains them all, even if it's
    useless at first glance, the linked pizza for each topping is mandotary to django to glue topping <=> pizza relationship.

    so, be carefull whene using prefetch_related.



specific comportments
---------------------

some specific behaviour has been implemented to use the extra functionnality of a Rest API :

- whene inserting, the resulting model is returned by the API. the inserted model is updated with the resulting values.
  this imply 2 behavior:

  * if you provided a default data in the api, this data will be populated into your created instance if it was missed
  * if the serializer have some cumputed data, its data will always be used as a replacment of the one you gave to your
    models. (see exemple Pizza.cost which is the sum of the cost of the toppling. after each save, its value will be updated)


support
-------

this database api support :

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

    ForeignKey must have db_colum fixed to the name of the field in the api. or all update/create won't use
    the value if this field

Documentation
-------------

The full documentation is at http://django-rest-models.readthedocs.org/en/latest/.


Requirements
------------

- Python 2.7, 3.4, 3.5
- Django >= 1.8

Contributions and pull requests for other Django and Python versions are welcome.


Bugs and requests
-----------------

If you have found a bug or if you have a request for additional functionality, please use the issue tracker on GitHub.

https://github.com/Yupeek/django-rest-models/issues


License
-------

You can use this under GPLv3.

Author
------

Original author: `Darius BERNARD <https://github.com/ornoone>`_.


Thanks
------

Thanks to django for this amazing framework.
