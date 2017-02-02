specials cases
##############


prefetch_related
****************


the prefetch related is a django optimisation for queryset that query the database for all given manytomany relation
to cache it in the model. this feature work in django-rest-models backend, but the remote api will return far more
data than the SQL equivalent should.

to prevent a performance issues in the api, django-rest-models will add a special get parameter in his query «filter_to_prefetch» which
can be interpreted by the backend to filter all sub-query with the actual id.

a small tricks in the api side is to override the DynamicFilterBackend with the folowing class, and use it in your views.

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


to use this new FilterBackend, you can write your view like this

.. code-block:: python

    class CompanyViewSet(DynamicModelViewSet):
        serializer_class = CompanySerializer
        queryset = Company.objects.all()
        filter_backends = (PrefetchRelatedCompatibleFilterBackend, DynamicSortingFilter)

the `filter_backends` attribute is inherited from the WithDynamicViewSetMixin mixin. replace the `DynamicFilterBackend`
with your override