Testing
#######

.. _testing:

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