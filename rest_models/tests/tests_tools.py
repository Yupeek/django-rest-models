# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import datetime

from django.db import NotSupportedError, OperationalError
from django.test import TestCase

from rest_models.backend.compiler import (ApiResponseReader, QueryParser, SQLCompiler, build_aliases_tree,
                                          join_aliases, join_results, resolve_tree)
from testapi import models as api_models
from testapp import models as client_models


class TestResponseReader(TestCase):
    json_data = {
        'pizzas': [{'id': 1, 'links': {'menu': 'menu/'}, 'toppings': [1, 2, 3, 4, 5]},
                   {'id': 2, 'links': {'menu': 'menu/'}, 'toppings': [1, 4]},
                   {'id': 3, 'links': {'menu': 'menu/'}, 'toppings': [1, 4, 6]}],
        'toppings': [{'id': 1, 'name': 'crème'},
                     {'id': 2, 'name': 'tomate'},
                     {'id': 3, 'name': 'olive'},
                     {'id': 4, 'name': 'lardon'},
                     {'id': 5, 'name': 'champignon'},
                     {'id': 6, 'name': 'foie gras'}]
    }

    def setUp(self):
        self.reader = ApiResponseReader(self.json_data)

    def test_get(self):
        self.assertEqual(self.reader[client_models.Pizza][1],
                         {'id': 1, 'links': {'menu': 'menu/'}, 'toppings': [1, 2, 3, 4, 5]})
        self.assertEqual(self.reader[client_models.Pizza][2],
                         {'id': 2, 'links': {'menu': 'menu/'}, 'toppings': [1, 4]})

    def test_other_model(self):
        self.assertEqual(self.reader[client_models.Topping][1], {'id': 1, 'name': 'crème'})

    def test_model_not_in_response(self):
        self.assertRaises(OperationalError, lambda a, b: a[b], self.reader, client_models.Bookmark)

    def test_model_not_api(self):
        self.assertRaises(OperationalError, lambda a, b: a[b], self.reader, api_models.Pizza)


class TestJoinGenerator(TestCase):
    json_data = {
        'menus': [
            {'code': 'mn',
             'id': 1,
             'name': 'main menu',
             'pizzas': [1],
             },
            {'code': 'cde',
             'id': 2,
             'name': '2nd menu',
             'pizzas': [2, 3],
             }
        ],
        'pizzas': [{'id': 1, 'menu': 1, 'toppings': [1, 2, 3, 4, 5]},
                   {'id': 2, 'menu': 2, 'toppings': [1, 4]},
                   {'id': 3, 'menu': 2, 'toppings': [1, 4, 6]}],
        'toppings': [{'id': 1, 'name': 'crème'},
                     {'id': 2, 'name': 'tomate'},
                     {'id': 3, 'name': 'olive'},
                     {'id': 4, 'name': 'lardon'},
                     {'id': 5, 'name': 'champignon'},
                     {'id': 6, 'name': 'foie gras'}]
    }

    def assertJoinEqual(self, queryset, expected, current_obj_pk):
        reader = ApiResponseReader(self.json_data)
        qs = queryset

        compiler = SQLCompiler(qs.query, None, 'api')
        compiler.setup_query()
        resources, fields_path = compiler.query_parser.get_resources_for_cols([col for col, _, _ in compiler.select])

        current_obj = reader[qs.model][current_obj_pk]
        tree = build_aliases_tree(resources)

        aliases_list = list(resolve_tree(tree))
        results = list(join_aliases(aliases_list, reader, {tree.alias: current_obj}))
        formated_results = [
            {
                alias.model.__name__: val
                for alias, val in d.items()
            }
            for d in results
        ]
        self.assertEqual(formated_results, expected)

    def test_join_alias_resolution(self):
        self.assertJoinEqual(
            client_models.Pizza.objects.values('id', 'toppings__name'),
            [
                {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 1, 'name': 'crème'}
                }, {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 2, 'name': 'tomate'}
                }, {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 3, 'name': 'olive'}
                }, {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 4, 'name': 'lardon'}
                }, {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 5, 'name': 'champignon'}
                },
            ],
            1
        )

    def test_join_alias_one_join(self):
        self.assertJoinEqual(
            client_models.Pizza.objects.values('id'),
            [
                {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                }
            ],
            1
        )

    def test_join_alias_fk_on_value(self):
        self.assertJoinEqual(
            client_models.Menu.objects.values('id', 'pizzas__menu'),
            [
                {
                    'Menu': {'code': 'mn',
                             'id': 1,
                             'name': 'main menu',
                             'pizzas': [1],
                             },
                    'Pizza': {'id': 1, 'menu': 1, 'toppings': [1, 2, 3, 4, 5]},
                }
            ],
            1
        )

    def test_join_alias_backward_on_value(self):
        self.assertJoinEqual(
            client_models.Pizza.objects.values('id', 'menu__name'),
            [
                {
                    'Menu': {'code': 'mn',
                             'id': 1,
                             'name': 'main menu',
                             'pizzas': [1],
                             },
                    'Pizza': {'id': 1, 'menu': 1, 'toppings': [1, 2, 3, 4, 5]},
                }
            ],
            1
        )

    def test_join_alias_manymany(self):
        self.assertJoinEqual(
            client_models.Pizza.objects.values('id', 'toppings__name'),
            [
                {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 1, 'name': 'crème'}
                }, {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 2, 'name': 'tomate'}
                }, {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 3, 'name': 'olive'}
                }, {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 4, 'name': 'lardon'}
                }, {
                    'Pizza': {'id': 1, 'toppings': [1, 2, 3, 4, 5], 'menu': 1},
                    'Topping': {'id': 5, 'name': 'champignon'}
                }
            ],
            1
        )

    def test_join_result(self):
        aliases = QueryParser(client_models.Topping.objects.values('pizzas__menu__name').query).aliases
        resolved = [
            (aliases['testapp_pizza'], 'menu'),
            (aliases['testapp_topping'], 'pizzas'),
        ]
        row = {
            aliases['testapp_pizza']: {'menu': 1},
            aliases['testapp_topping']: {'pizzas': [1, 2, 3]},
        }
        self.assertEqual(
            list(join_results(row, resolved)),
            [
                [1, 1],
                [1, 2],
                [1, 3],
            ]
        )

    def test_join_result_bad_type(self):
        aliases = QueryParser(client_models.Topping.objects.values('pizzas__menu__name').query).aliases
        resolved = [
            (aliases['testapp_pizza'], 'menu'),
            (aliases['testapp_topping'], 'pizzas'),
        ]
        row = {
            aliases['testapp_pizza']: {'menu': 1},
            aliases['testapp_topping']: {'pizzas': datetime.date.today()},
        }
        self.assertRaisesMessage(NotSupportedError, "the result from the api ", list, join_results(row, resolved))
