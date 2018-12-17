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

