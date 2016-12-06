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

specials urls
-------------

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

on each api models, a nested class named APIMeta must be attached to the model.
this class can contains some customisation for the model.

exemple::

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

provide the name of the database conexion in which thi model is placed.
if there is only one database connexion that use rest_models backend, it is optional.
if there is more than one connexion with this backend, all models MUST give this setting on APIMeta

resource_path
=============

the value to append to the path of the api to get the endpoint of this model.
in many cases, it's the «verbose_name» on the api side. or the value given in the router:

.. code-block:: python

    router = DynamicRouter()
    router.register('pizza', PizzaViewSet)  # this match the verbose_name of Pizza... default behavior will work
    router.register('topping', ToppingViewSet)
    router.register('menulol', MenuViewSet)  # «menulol» for path. must be specified since menulol don't match verbose_name

resource_name
=============

the value for the serializer.Meta.name

.. code-black:: python


    class PizzaSerializer(DynamicModelSerializer):

        class Meta:
            model = Pizza
            name = 'pizza' # ressource name match the verbose_name of the model. no need to customise ressource_name


resource_name_plural
====================

this is the plural variant of resource_name. if the resource_name is customized, you will need to customize this too.
in many cases, it will resource_name + 's'

.. code-black:: python


    class PizzaSerializer(DynamicModelSerializer):

        class Meta:
            model = Pizza
            name = 'pizza' # ressource name match the verbose_name of the model. no need to customise ressource_name_plural


