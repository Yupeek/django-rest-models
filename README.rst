==================
django-rest-models
==================

allow to query an RestAPI (django-rest-framework + dynamic-rest) with same same interface as the django ORM.
if fact, it work like any other database engin. you add the rest_models engin in an alternate database, the router, and
add a APIMeta class to your models, and let's go.


.. image:: https://img.shields.io/travis/Yupeek/django-rest-models/master.svg
    :target: https://travis-ci.org/Yupeek/django-rest-models

.. image:: https://readthedocs.org/projects/django-rest-models/badge/?version=latest
    :target: http://django-rest-models.readthedocs.org/en/latest/

.. image:: https://coveralls.io/repos/github/Yupeek/django-rest-models/badge.svg?branch=develop
    :target: https://coveralls.io/github/Yupeek/django-rest-models?branch=develop


.. image:: https://img.shields.io/pypi/v/django-rest-models.svg
    :target: https://pypi.python.org/pypi/django-rest-models
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/django-rest-models.svg
    :target: https://pypi.python.org/pypi/django-rest-models
    :alt: Number of PyPI downloads per month



Installation
------------

1. Install using pip:

   ``pip install django-rest-models``

2. Alternatively, you can install download or clone this repo and call

    ``pip install -e .``.

exemples
--------

settings.py::

    DATABASES = {
        'default': {
            ...
        },
        'api': {
            'ENGINE': 'rest_models.backend',
            'NAME': 'https://requestb.in/',
            'USER': 'userapi',
            'PASSWORD': 'passwordapi',
            'AUTH': 'rest_models.backend.auth.basic',
        },
    }

    DATABASE_ROUTERS = [
        'rest_models.router.RestModelRouter',
    ]

models.py::

    class MyModel(models.Model):
        field = models.IntegerField()
        ...

        class Meta:
            # basic django meta Stuff
            verbose_name = 'my model'

        # the only customisation that make this model special
        class APIMeta:
            pass


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
