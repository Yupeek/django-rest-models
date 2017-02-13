# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging

from django.db.backends.base.introspection import BaseDatabaseIntrospection, FieldInfo, TableInfo

logger = logging.getLogger(__name__)


class DatabaseIntrospection(BaseDatabaseIntrospection):
    features = {
        "include[]",
        "exclude[]",
        "filter{}",
        "page",
        "per_page",
        "sort[]"
    }

    data_types_reverse = {
        'integer': 'IntegerField',
        'string': 'CharField',
        'date': 'DateField',
        'float': 'FloatField',
        'datetime': 'DateTimeField',
        'many': 'ManyToMany',
        'one': 'ForeignKey',
        'field': 'ManyToMany'
    }

    def get_indexes(self, cursor, table_name):
        return []

    def get_table_list(self, cursor):
        res = cursor.get('', params={'format': 'json'})
        if res.status_code != 200:
            raise Exception("error while querying the table list %s: "
                            "[%s] %s" % (res.request.url, res.status_code, res.text[:500]))
        tables = res.json().keys()
        for table in tables:
            response = cursor.options(table)
            if response.status_code != 200:
                raise Exception("bad response from api: %s" % response.text)
            option = response.json()
            missing_features = self.features - set(option['features'])
            if missing_features:
                raise Exception("the remote api does not provide all required features : %s" % missing_features)

        return [
            TableInfo(t, 't')
            for t in tables
        ]

    def get_constraints(self, cursor, table_name):
        return {}

    def get_relations(self, cursor, table_name):
        res = cursor.get(
            table_name,
            params={'page': 1, 'per_page': 1}
        )
        if res.status_code != 200:
            raise Exception("the remote api failed our query on %s : [%s]%s" %
                            (table_name, res.status_code, res.text))
        data = res.json()

        ressource_name = list(set(data.keys()) - {'meta'})[0]
        try:
            obj = data[ressource_name][0]
        except IndexError as ie:
            logger.exception("can't introspect %s. there is no data in the api for this model." % (ressource_name,))
            obj = {}

        return {
            k: ('id', v.rstrip("/"))
            for k, v in obj.get('links', {}).items()
            }

    def get_table_description(self, cursor, table_name):
        options = cursor.options(table_name).json()
        fields = options['properties']

        return [
            FieldInfo(name, descr['type'], None, None, None, None, descr['nullable'])
            for name, descr in fields.items()
        ]
