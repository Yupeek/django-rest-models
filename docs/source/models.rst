.. _models:

build your client models
########################



to build your models based on the one on the api, it pretty simple.

your api models look like this:


.. code-block:: python

    from django.db import models
    from django.contrib.postgres.fields import JSONField


    class Menu(models.Model):
        name = models.CharField(max_length=135)
        code = models.CharField(max_length=3)


        def __str__(self):
            return self.name  # pragma: no cover

    class Pizza(models.Model):

        name = models.CharField(max_length=125)
        price = models.FloatField()
        from_date = models.DateField(auto_now_add=True)
        secret_ingredient = models.CharField(max_length=125)
        metadata = JSONField(null=True)


        menu = models.ForeignKey(Menu, null=True, related_name='pizzas')

        photo = models.ImageField(upload_to='/images/')

        def __str__(self):
            return self.name  # pragma: no cover



0. copy/past the model class from the api to your own models.py

1. add the APIMeta to your each model class. see See :ref:`APIMeta` section to know how you can customize it.


.. code-block:: python

    from django.db import models
    from django.contrib.postgres.fields import JSONField


    class Menu(models.Model):
        name = models.CharField(max_length=135)
        code = models.CharField(max_length=3)

        def __str__(self):
            return self.name  # pragma: no cover


        class APIMeta:
            pass

    class Pizza(models.Model):

        name = models.CharField(max_length=125)
        price = models.FloatField()
        from_date = models.DateField(auto_now_add=True)
        secret_ingredient = models.CharField(max_length=125)
        metadata = JSONField(null=True)

        menu = models.ForeignKey(Menu, null=True, related_name='pizzas')

        photo = models.ImageField(upload_to='/images/')

        def __str__(self):
            return self.name  # pragma: no cover

        class APIMeta:
            pass


2. comment/remove the fields which is not exposed in the serializer of the models in your api

from:

.. code-block:: python

    class Pizza(models.Model):

        ...
        secret_ingredient = models.CharField(max_length=125)
        ...


to:

.. code-block:: python

    class Pizza(models.Model):

        ...
        # this sensitive data is not exposed by the api, we can't use it on the client.
        # secret_ingredient = models.CharField(max_length=125)
        ...


3.  change all ForeignKey by adding a db_column equivalent to the field name itself.


from:

.. code-block:: python


    class Menu(models.Model):
        ...


    class Pizza(models.Model):


        menu = models.ForeignKey(Menu, null=True, related_name='pizzas')
        ...


to:

.. code-block:: python


    class Menu(models.Model):
        ...


    class Pizza(models.Model):


        menu = models.ForeignKey(Menu, null=True, related_name='pizzas', db_column='menu')
        ...


4. change all ImageField/FileField to add our custom storage which handle upload to api


.. code-block:: python

    from rest_models.storage import RestApiStorage
    ...

    class Pizza(models.Model):
        ...

        photo = models.ImageField(storage=RestApiStorage())
        ...

5. change all JSONField from django.contrib.postgres.fields to use our custom field.
  our custom field just handle the get_prep_value to make it compatible with our backend.

.. code-block:: python

    from rest_models.backend.utils import JSONField

    ...

    class Pizza(models.Model):

        ...
        metadata = JSONField(null=True)
        ...



6. enjoy your new model, which should look like this:

.. code-block:: python

    from django.db import models
    from rest_models.storage import RestApiStorage
    from rest_models.backend.utils import JSONField


    class Menu(models.Model):
        name = models.CharField(max_length=135)
        code = models.CharField(max_length=3)


        def __str__(self):
            return self.name  # pragma: no cover


        class APIMeta:
            db_name = 'api'

    class Pizza(models.Model):

        name = models.CharField(max_length=125)
        price = models.FloatField()
        from_date = models.DateField(auto_now_add=True)
        # this sensitive data is not exposed by the api, we can't use it on the client.
        # secret_ingredient = models.CharField(max_length=125)
        metadata = JSONField(null=True)

        menu = models.ForeignKey(Menu, null=True, related_name='pizzas', db_column='menu')

        photo = models.ImageField(storage=RestApiStorage())

        def __str__(self):
            return self.name  # pragma: no cover


        class APIMeta:
            db_name = 'api'

