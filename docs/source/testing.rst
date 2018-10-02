.. _testing:

Testing
#######

localapi
********

to write tests using the api database, Rest Model allow you to bypass the usage of a remote API to loopback into the
local process for the api query. if the host of the api is ``localapi``, Rest Model will not go to the network seeking
an host named ``localapi`` but will query the local url engine to fetch the serializers.
if you have your API application installed as local dependecies for testing, and an url running with it, you can
write tests painelessly.

this allow:

- database transaction on all request made to the api
- faster testing since no network stack is used
- easier testing setup, since no api should be started before the tests

by default, the test database for api will use the ``localapi`` system. to bypass this, provide a ``DATABASES`` config
named ``TEST_{name}``. this database will be used for all query on the api database *{name}*

.. code-block:: python

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sq3',
        },
        'api': {
            'ENGINE': 'rest_models.backend',
            'NAME': 'http://localapi/api/v2',
            'USER': 'admin',
            'PASSWORD': 'admin',
            'AUTH': 'rest_models.backend.auth.BasicAuth',
        },

        'TEST_api': {  # replace the database «api» durring the tests
            'ENGINE': 'rest_models.backend',
            'NAME': 'http://localhost:8080/api/v2',
            'USER': 'userapi',
            'PASSWORD': 'passwordapi',
            'AUTH': 'rest_models.backend.auth.BasicAuth',
            'OPTIONS': {
                'SKIP_CHECK': True,
            },
        },
    }

Mock API
********


overview
========


you can mock the api with some custom response for given url. it won't trigger any api query, but return the
predefined data from each request matching the patterns.

your test cases must inherit from either ``rest_models.test.RestModelTestMixin`` or
``rest_models.test.RestModelTestCase``

with this, you have 2 more functionnality.

you can provide the matching «url» => «response» by giving the ``rest_fixtures`` like this:

.. code-block:: python

    class TestAnnonymousVisit(RestModelTestMixin, TestCase):

        rest_fixtures = {
            '/oauth2/token/': [
                {'data': {'scope': 'read write', 'access_token': 'HJKMe81faowKipJGKZSwg05LnfJmrU',
                                        'token_type': 'Bearer', 'expires_in': 36000}}
            ],
            '/pizzas/': 'path/to/fixtures.json',
        }

with the file in ``path/to/fixtures.json`` :

.. code-block:: python

    [
      {
        "filter": {},
        "data": {
          "pizza": {
            "cost": 2.08,
            "to_date": "2016-11-20T08:46:02.016000",
            "from_date": "2016-11-15",
            "price": 10.0,
            "id": 1,
            "links": {
              "toppings": "toppings/"
            },
            "name": "suprème",
            "toppings": [
              1,
              2,
              3,
              4,
              5
            ],
            "menu": 1
          }
        }
      }
    ]


providing data
==============

global to the tests
-------------------


if you have 2 or more api databases, you must provide a mapping `database` => `fixtures` in the static attribute
``database_rest_fixtures``. if you have only one api database, the ``database_rest_fixtures`` is automaticaly mapped
to the default one:

.. code-block:: python

    class TestAnnonymousVisit(RestModelTestMixin, TestCase):


        database_rest_fixtures = {'api': {  # api is our first database
            '/oauth2/token/': [
                {'data': {'scope': 'read write', 'access_token': 'HJKMe81faowKipJGKZSwg05LnfJmrU',
                                        'token_type': 'Bearer', 'expires_in': 36000}}
            ],
        }}


local to a function
-------------------

you can temporary mock the data from the api by using ``RestModelTestMixin.mock_api`` context manager

.. code-block:: python

    class TestAnnonymousVisit(RestModelTestMixin, TestCase):

        def test_remote_name_mismatch(self):

            with self.mock_api('pizza', {'pizzas': []}, using='api'):
                self.assertEqual(len(list(Pizza.objects.all())), 0)


it take 3 arguments :

- url: the url to mock
- result : the result to return for the given url
- params: the params that will be used to filter the usage of this mock
- using: optionnaly the api to mock, if there is more than one


data structure
==============

the structure of the mocked data is a list of possible results, represented by a dict with 2 keys :

- data: the actual data returned by the api if it was queried (``{"pizzas": [...], "menus": [...]}``)
- filter: for the given data to be used, the query must match this dict of data
- statuscode: the status code to simulate

data
----

the data is a copy past of the real result expeced in the api.

the fowoing is extracted from the rest api interface and is a valid ``data`` value

.. code-block:: json

    {
        "pizzas": [
            {
                "links": {
                    "toppings": "toppings/"
                },
                "to_date": "2016-11-20T08:46:02.016000",
                "price": 10.0,
                "cost": 2.08,
                "name": "suprème",
                "from_date": "2016-11-15",
                "toppings": [
                    1,
                    2,
                    3,
                    4,
                    5
                ],
                "menu": 1,
                "id": 1
            },

        ],
        "meta": {
            "per_page": 10,
            "total_pages": 1,
            "page": 1,
            "total_results": 1
        }
    }

filter
------

the filter is a dict or a list of dict that can be empty, in that case it will match all query.
it can contains one of the folowing revelent value. any other will make this dataset unmatching all query.
if it's a list, any dict inside that match the query will validate this fixtures.


- params: the main filter helper. it must contains a dict with the query parameters in the get for the api
- method: the method used (get, post, put, ...)
- json: the posted data


params
^^^^^^

the params filters is a dict with each item the part of the final query GET to the api.


for exemples :

``?filter{name}=lolilol&filter{pizza.name}=pipi`` =>

.. code-block:: python

    {'params': {'filter{name}': 'lolilol', 'filter{pizza.name}': 'pipi'}}



json
^^^^

the json must match the posted/puted data if given.
if you created a Menu with name='hey' :

.. code-block:: python

    'filter': {
        'method': 'post',
        'json': {'menu': {'name': 'hey'}}  # posted data must match this
    },

.. note::

    remember that all posted data must return a 201 status code ::

        {  # response for post
            'filter': {
                'method': 'post',
                ...
            },
            'data': {  # this will return a fake models created response
                ...
            },
            'status_code': 201  # the mandatory statuscode to return for a post success
        },


full example
============

the folowing test case is a full example taken from the test suit. it's a good point for start.

.. code-block:: python


    class TestMockDataSample(RestModelTestCase):
        database_rest_fixtures = {'api': {  # api => response mocker for databasen named «api»
            'menulol': [  # url menulol
                {
                    'filter': {  # set of filters to match
                        'params': {  # params => requests parameters to sort[],exclude[],filter{...},include[]
                            'filter{name}': ['lolilol'],  # with filter(name='lolilol')
                            'sort[]': ['-name']  # with order_by('-name')
                        }
                    },
                    'data': {
                        "menus": [],
                        "meta": {
                            "per_page": 10,
                            "total_pages": 1,
                            "page": 1,
                            "total_results": 0
                        }
                    }
                },
                {
                    'filter': [{
                        'params': {
                            'filter{name}': ['lolilol'],  # just the filter, no sorting
                        }
                    }],
                    'data': {
                        "menus": [
                            {
                                "links": {
                                    "pizzas": "pizzas/"
                                },
                                "id": 1,
                                "pizzas": [
                                    1
                                ],
                                "name": "main menu",
                                "code": "mn"
                            }
                        ],
                        "meta": {
                            "per_page": 10,
                            "total_pages": 1,
                            "page": 1,
                            "total_results": 1
                        }
                    }
                },
                {  # response for post
                    'filter': {
                        'method': 'post',
                        'json': {'menu': {'name': 'hey'}}  # posted data must match this
                    },
                    'data': {  # this will return a fake models created response
                        "menu": {
                            "id": 1,
                            "pizzas": [],
                            "name": "hey",
                            "code": "hy"
                        }
                    },
                    'status_code': 201  # the mandatory statuscode to return for a post success
                },
                {  # response for post
                    'filter': {
                        'method': 'post',
                    },
                    'data': {
                        "menu": {
                            "id": 2,
                            "pizzas": [],
                            "name": "hello",
                            "code": "ho"
                        }
                    },
                    'status_code': 201
                },
                {  # fallback
                    'filter': {},  # no filter => fallback
                    'data': {
                        "menus": [
                            {
                                "links": {
                                    "pizzas": "pizzas/"
                                },
                                "id": 1,
                                "pizzas": [
                                    1
                                ],
                                "name": "lolilol",
                                "code": "mn"
                            },
                            {
                                "links": {
                                    "pizzas": "pizzas/"
                                },
                                "id": 2,
                                "pizzas": [
                                    2
                                ],
                                "name": "lolilol",
                                "code": "ll"
                            }
                        ],
                        "meta": {
                            "per_page": 10,
                            "total_pages": 1,
                            "page": 1,
                            "total_results": 2
                        }
                    }

                }
            ]
        }}

        def test_multi_results_filter(self):
            # no filter/no sort => fallback
            self.assertEqual(len(list(Menu.objects.all())), 2)
            # no matching filter => fallback
            self.assertEqual(len(list(Menu.objects.filter(code='pr'))), 2)
            # no matching filter => fallback
            self.assertEqual(len(list(Menu.objects.filter(name='pr'))), 2)
            # matching filter/no sort => don't care for missing sort and return 1rst
            self.assertEqual(len(list(Menu.objects.filter(name='lolilol'))), 1)
            # no matching sort => 2nd found
            self.assertEqual(len(list(Menu.objects.filter(name='lolilol').order_by('name'))), 1)
            # no matching sort => 1st found
            self.assertEqual(len(list(Menu.objects.filter(name='lolilol').order_by('-name'))), 0)
            # no matching filter => fallback
            self.assertEqual(len(list(Menu.objects.filter(name='pr').order_by('-name'))), 2)

        def test_post_filter(self):
            # no filter/no sort => fallback
            m = Menu.objects.create(name='hey', code='!!')
            self.assertEqual(m.pk, 1)
            self.assertEqual(m.name, 'hey')
            self.assertEqual(m.code, 'hy')

            m = Menu.objects.create(name='prout', code='??')
            self.assertEqual(m.pk, 2)
            self.assertEqual(m.name, 'hello')
            self.assertEqual(m.code, 'ho')
