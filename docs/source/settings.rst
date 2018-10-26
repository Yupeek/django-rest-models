Settings
########



Some custom settings are available to customise the behavior of rest_models.

DATABASES setting
*****************

Example of many settings::

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
                'SKIP_CHECK': True,
            },
            'PREVENT_DISTINCT': False,
        },
        'TEST_api2': {
            'ENGINE': 'rest_models.backend',
            'NAME': 'http://localhost:8080/api/v2',
            'USER': 'userapi',
            'PASSWORD': 'passwordapi',
            'AUTH': 'rest_models.backend.auth.BasicAuth',
        },
    }

The database setting for the engine rest_models.backends accept the folowing values :


``NAME``
========

This settings give the url to the api root. it must be a http/https url that can have a path.

The path must be the one that give you a 200 status code with the list of serializers.

Examples :

- ``http://127.0.0.1:8001/api/v2/``
- ``https://api.mysite.org/``
- ``http://customhost/api/``

Special urls
------------

The special host `localapi` can be provided to bypass the network and redirect the connection on the local running
process in the same way as django do during tests (via Client). This allow to test against an api database without
having to make it run before the tests, and allow the transactions to work for unit-testing.
See :ref:`testing`

Example:

- ``http://localapi/api/v2``
- ``http://localapi/``

This will make requests to the local API system, rather than via the network to a remote system.


``USER``
========

The settings ``USER`` may be used by the ``AUTH`` backend. This depends on the backend used. Can be
empty if the backend doesn't need it or if there is no backend (public api)

``PASSWORD``
============

Like ``USER`` it can be used by the ``AUTH`` backend

``AUTH``
========

The path to the ``ApiAuthBase`` subclass that will be used to provide the authentication header to the api.
Each query will __call__ this subclass with the ``requests.Request`` object and shall update the header to
provide the data for authentications.

The following backends are shiped with rest_models:

``rest_models.backend.auth.BasicAuth``
--------------------------------------

Provide the Basic authentication with ``USER`` and ``PASSWORD``

``rest_models.backend.auth.OAuthToken``
---------------------------------------

Provide the OAuth2 authentication.  This will fetch a token using ``USER`` and
``PASSWORD`` each time it's expired, and provide the API with the header ``Authorization: Bearer <token>``

This backend can use extra settings in ``OPTIONS`` named ``OAUTH_URL`` which is the endpoint to the Oauth2
token provider. By default this url is ``/oauth2/token/``.


``OPTIONS['TIMEOUT']``
======================

Provide the time for triggering a new query on the api. If a query take longer than this, it will retry 3 more times,
and eventialy raise an OperationalError.

``OPTIONS['SKIP_CHECK']``
======================

Will skip checking the api if this settings is set to true. By default, the Django check command
(executed during tests and migration) will query the api to check if our models match the structure of the api.
Settings this to True will prevent any query to be made to the api.  This is useful for testing environments where
all queries are faked and there is no api at all.

``PREVENT_DISTINCT``
====================

This settings allow to accept request with a `distinct` clause without raising an Exception.
Note that the distinct stuff will be trashed and the final query may repeat his lines.
Enable it if you know what you are doing.


APIMeta
*******

On each api models, a nested class named APIMeta must be attached to the model.
This class can contain some customisation for the model.

Example::

    class Menu(models.Model):
        name = models.CharField(max_length=135)
        code = models.CharField(max_length=3)

        class APIMeta:
            db_name = 'api'
            resource_path = 'menulol/'
            resource_name = 'menu'
            resource_name_plural = 'menus'


db_name
=======

Provide the name of the database connection in which this model is placed.
If there is only one database connection that use rest_models backend, it is optional.
If there is more than one connection with this backend, all models MUST give this setting on APIMeta

resource_path
=============

The value to append to the path of the api to get the endpoint of this model.
In many cases, it's the «verbose_name» on the api side. or the value given in the router:

.. code-block:: python

    router = DynamicRouter()
    router.register('pizza', PizzaViewSet)  # this match the verbose_name of Pizza... default behavior will work
    router.register('topping', ToppingViewSet)
    router.register('menulol', MenuViewSet)  # «menulol» for path. must be specified since menulol don't match verbose_name

resource_name
=============

The value for the serializer.Meta.name

.. code-block:: python


    class PizzaSerializer(DynamicModelSerializer):

        class Meta:
            model = Pizza
            name = 'pizza' # resource name match the verbose_name of the model. no need to customise resource_name


resource_name_plural
====================

This is the plural variant of resource_name. If the resource_name is customized, you will need to customize this too.
In many cases, it will resource_name + 's'

.. code-block:: python


    class PizzaSerializer(DynamicModelSerializer):

        class Meta:
            model = Pizza
            name = 'pizza' # resource name match the verbose_name of the model. no need to customise resource_name_plural


