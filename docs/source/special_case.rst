Special cases
#############


prefetch_related
****************


The `prefetch_related` method is a Django optimisation for querysets that
causes the database to cache the related fields for all given manytomany
relation in the model. This feature works in django-rest-models
backend, but the remote api will return far more data than the SQL equivalent
should.

To prevent performance issues in the api, django-rest-models will add a special
get parameter «filter_to_prefetch» in the query which can be interpreted by the
backend to filter all sub-query with the actual id.

A small trick in the api side is to override the DynamicFilterBackend with the following class, and use it in your views.

.. code-block:: python


    class PrefetchRelatedCompatibleFilterBackend(DynamicFilterBackend):
        def _build_requested_prefetches(
                self,
                prefetches,
                requirements,
                model,
                fields,
                filters
        ):
            # hack that apply the original filters on the responses from a

            prefetch = super(PrefetchRelatedCompatibleFilterBackend, self)._build_requested_prefetches(
                prefetches,
                requirements,
                model,
                fields,
                filters
            )
            if self.request.GET.get('filter_to_prefetch'):
                for field in prefetch:
                    in_ = filters.get('_include', {}).get('%s__in' % field)
                    if in_:
                        prefetch[field].queryset = prefetch[field].queryset.filter(pk__in=in_.value)
            return prefetch


To use this new FilterBackend, you can write your view like this

.. code-block:: python

    class CompanyViewSet(DynamicModelViewSet):
        serializer_class = CompanySerializer
        queryset = Company.objects.all()
        filter_backends = (PrefetchRelatedCompatibleFilterBackend, DynamicSortingFilter)

the `filter_backends` attribute is inherited from the WithDynamicViewSetMixin mixin. replace the `DynamicFilterBackend`
with your override

Many2Many creation/update
*************************


The special case of many2many fields is that they use a table that is not serialized by default in the api.
The query system can pass through it without this requirement, but the modification of a M2M require the update of the
through table. To do so, the best way is to serialize this table in the api and manipulate it as a standalone relation
in the application, without the ``myobject.myrelation.add()`` call.

For example, the link pizza <-> topping use the auto created relation Pizza_toppings

This requires the creation of the serializer and viewset for this auto created model in the api:

.. code:: python

  # serializer.py
  # many2many through serializer
  class PizzaToppingsSerializer(DynamicModelSerializer):
    class Meta:
      model = Pizza._meta.get_field('toppings').rel.through
      name = 'Pizza_topping'
      fields = ('id', 'pizza', 'topping',)

    topping = DynamicRelationField('ToppingSerializer', many=False, required=False)
    pizza = DynamicRelationField('PizzaSerializer', many=False, required=False)

  # models.py
  class Pizza_toppingsViewSet(DynamicModelViewSet):
    serializer_class = PizzaToppingsSerializer
    queryset = PizzaToppingsSerializer.get_model().objects.all()


  # urls.py
  router.register('Pizza_topping', Pizza_toppingsViewSet)

and the client should use it as any other model, without declaring it as a through model of Pizza and Topping

.. code:: python


  class Pizza_topping(models.Model):
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE, db_column='pizza', related_name='+')
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE, db_column='topping', related_name='+')

    class APIMeta:
      db_name = 'api'
      resource_name = 'Pizza_topping'
      resource_name_plural = 'Pizza_toppings'

    class Meta:
      auto_created = True
