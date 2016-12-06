settings
########



some custom settings are available to customise the behavior of rest_models.

DATABASES setting
*****************

exemple of many settings::

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
        'api2': {
            'ENGINE': 'rest_models.backend',
            'NAME': 'http://127.0.0.1:8001/api/v2/',
            'USER': 'pwd',
            'PASSWORD': 'pwd',
            'AUTH': 'rest_models.backend.auth.OAuthToken',
            'OPTIONS': {
                'OAUTH_URL': '/oauth2/token/',
                'TIMEOUT': 10,
            }
        },
        'TEST_api2': {
            'ENGINE': 'rest_models.backend',
            'NAME': 'http://localhost:8080/api/v2',
            'USER': 'userapi',
            'PASSWORD': 'passwordapi',
            'AUTH': 'rest_models.backend.auth.BasicAuth',
        },
    }

the database setting for the engin rest_models.backends accept the folowing values :


``NAME``
========

this settings give the url to the api root. it must be a http/https url that can have a path.

the path must be the one that give you a 200 status code with the list of serializers.

exemples :

- ``http://127.0.0.1:8001/api/v2/``
- ``https://api.mysite.org/``
- ``http://customhost/api/``

-------------
specials urls

the special host `localapi` can be provided to bypass the network and redirect the connection on the local running
process in the same way as django do durring tests (via Client). this allow to test against a api database without
having to make it run befor the tests, and allow the transactions to work for unit-testing.
see :ref:`testing`

exemple:

- ``http://localapi/api/v2``
- ``http://localapi/``

this will lookup for local url.


``USER``
========

the settings ``USER`` may be used by the ``AUTH`` backend. this depend on the backend used. can be
empty if the backend don't need it or if there is no backend (public api)

``PASSWORD``
============

like ``USER`` it can be used by the ``AUTH`` backend

``AUTH``
========

the path to the ``ApiAuthBase`` subclass that will be used to provide the authentication header to the api.
each query will __call__ this subclass with the ``requests.Request`` object and shall update his header to
provide the data for authentications.

the following backend is shiped with rest_models:

``rest_models.backend.auth.BasicAuth``
--------------------------------------

provide the Basic authentication with ``USER`` and ``PASSWORD``

``rest_models.backend.auth.OAuthToken``
---------------------------------------

provide the OAuth2 authentication. will fetch a token using ``USER`` and
``PASSWORD`` each time it's expired, and provide the API with the header ``Authorization: Bearer <token>``

this backend can use extra settings in ``OPTIONS`` named ``OAUTH_URL`` which is the endpoint to the Oauth2
token provider. by default this url is ``/oauth2/token/``.


``OPTIONS['TIMEOUT']``
======================

provide the time for triggering a new query on the api. if a query take longer than this, it will retry 3 more times,
and eventialy raise an OperationalError.



APIMeta
*******



