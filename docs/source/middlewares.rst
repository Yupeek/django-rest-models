Middlewares
###########

the Rest Models Middlewares work like the django ones.
it intercept all query that will be sent to the api, and can update the params, or bypass the api and return
a result.


.. autoclass:: rest_models.backend.middlewares.ApiMiddleware
    :members:
