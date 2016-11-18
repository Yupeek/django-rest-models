# -*- coding: utf-8 -*-
from django.db.models.query_utils import Q
from django.db.utils import NotSupportedError
from django.test import TestCase
from rest_models.backend.compiler import SQLCompiler
from testapp.models import Pizza, Topping


class CompilerTestCase(TestCase):
    def assertQsToFilter(self, queryset, res):
        # fix the fact the the test test uniq value, but the
        # compiler return a dict of list (even if there is on element each times)
        for k, v in res.items():
            if not isinstance(v, list):
                res[k] = [v]
        self.assertEqual(SQLCompiler.build_filter_params(queryset.query), res)


    def assertBadQs(self, queryset):
        self.assertRaises(NotSupportedError, SQLCompiler.check_compatibility, queryset.query)


    def assertGoodQs(self, queryset):
        self.assertIsNone(SQLCompiler.check_compatibility(queryset.query))


class TestCompilerFilterParams(CompilerTestCase):

    def test_simple_filter(self):
        self.assertQsToFilter(
            Pizza.objects.filter(pk=1),
            {'filter{id}': 1}
        )

    def test_simple_exclude(self):
        self.assertQsToFilter(
            Pizza.objects.exclude(pk=1),
            {'filter{-id}': 1}
        )

    def test_anded_exclude(self):
        self.assertQsToFilter(
            Pizza.objects.exclude(pk=1, price=11.0),
            {'filter{-id}': 1, 'filter{-price}': 11.0},
        )
        self.assertQsToFilter(
            Pizza.objects.exclude(pk=1).exclude(price=11.0),
            {'filter{-id}': 1, 'filter{-price}': 11.0},
        )

    def test_and_filter(self):
        self.assertQsToFilter(
            Pizza.objects.filter(id=3, price=15.0),
            {'filter{id}': 3, 'filter{price}': 15.0},
        )
        self.assertQsToFilter(
            Pizza.objects.filter(id=3).filter(price=15.0),
            {'filter{id}': 3, 'filter{price}': 15.0},
        )

    def test_exclude_and_filter(self):
        self.assertQsToFilter(
            Pizza.objects.filter(id=3).exclude(price=11.0),
            {'filter{id}': 3, 'filter{-price}': 11.0},
        )
        self.assertQsToFilter(
            Pizza.objects.filter(Q(id=3) & ~Q(price=11.0)),
            {'filter{id}': 3, 'filter{-price}': 11.0},
        )

    def test_Q_with_and(self):
        self.assertQsToFilter(
            Pizza.objects.filter(Q(id=3), Q(price=15.0)),
            {'filter{id}': 3, 'filter{price}': 15.0},
        )
        self.assertQsToFilter(
            Pizza.objects.filter(Q(id=3) & Q(price=15.0)),
            {'filter{id}': 3, 'filter{price}': 15.0},
        )


class TestIncompatibleBuildCompiler(CompilerTestCase):

    def test_or_filter(self):
        self.assertBadQs(
            Pizza.objects.filter(Q(id=1) | Q(cost=10.0))
        )
        self.assertBadQs(
            Pizza.objects.exclude(Q(id=2) | Q(cost=15.0))
        )

    def test_negated_Q(self):
        # negate a AND give a OR, whiche is not supported
        self.assertBadQs(
            Pizza.objects.filter(~Q(Q(id=1) & Q(cost=10.0)))
        )
        self.assertBadQs(
            Pizza.objects.filter(~Q(id=1, cost=10.0))
        )

    def test_ok_filter(self):
        self.assertGoodQs(
            Pizza.objects.filter(Q(id=1) & Q(cost=10.0))
        )
        self.assertGoodQs(
            Pizza.objects.filter(Q(id=1) & ~Q(cost=10.0))
        )
        self.assertGoodQs(
            Pizza.objects.filter(Q(Q(id=1) & ~Q(cost=10.0)))
        )

    def test_unseported_mix(self):
        # negated OR give AND
        # but it's took complexe to detect
        self.assertBadQs(
            Pizza.objects.filter(~Q(Q(id=1) | ~Q(cost=10.0)))
        )


class TestLookupCompliler(CompilerTestCase):

    def test_in(self):
        self.assertQsToFilter(
            Pizza.objects.filter(id__in=[1, 2]),
            {'filter{id.in}': [1, 2]}
        )
        self.assertQsToFilter(
            Pizza.objects.exclude(id__in=[1, 2]),
            {'filter{-id.in}': [1, 2]}
        )

    def test_icontains(self):
        self.assertQsToFilter(
            Pizza.objects.filter(name__icontains='sup'),
            {'filter{name.icontains}': 'sup'}
        )
        self.assertQsToFilter(
            Pizza.objects.exclude(name__icontains='sup'),
            {'filter{-name.icontains}': 'sup'}
        )
