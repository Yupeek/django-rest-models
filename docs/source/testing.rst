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
        },
    }

Mock API
********


you can mock the api with some custom response for given url. it won't trigger any api query, but return the
predefined data from each request matching the patterns.

your test cases must inherite from either ``rest_models.test.RestModelTestMixin`` or
``rest_models.test.RestModelTestCase``

with this, you have 2 more functionnality.

you can provide the matching «url» => «response» by giving the ``rest_fixtures`` like this::

    class TestAnnonymousVisit(RestModelTestMixin, TestCase):

        rest_fixtures = {
                '/oauth2/token/': [
                    {'data': {'scope': 'read write', 'access_token': 'HJKMe81faowKipJGKZSwg05LnfJmrU',
                                            'token_type': 'Bearer', 'expires_in': 36000}}
                ],
                '/pizzas/': 'path/to/fixtures.json',
            }
        )

with the file in ``path/to/fixtures.json`` ::

    {
      "/pizza/1/": {
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
    }

