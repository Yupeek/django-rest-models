# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging
from random import randint

from django.db.models.sql.constants import MULTI, NO_RESULTS, SINGLE
from django.db.models.sql.compiler import SQLCompiler as BaseSQLCompiler

from rest_models.backend.exceptions import FakeDatabaseDbAPI2

logger = logging.getLogger(__name__)


class SQLCompiler(BaseSQLCompiler):
    def __init__(self, query, connection, using):
        """
        :param django.db.models.sql.query.Query query:
        :param rest_models.backend.base.DatabaseWrapper connection:
        :param str using:
        """
        self.query = query
        self.connection = connection
        self.using = using
        self.quote_cache = {'*': '*'}
        # The select, klass_info, and annotations are needed by QuerySet.iterator()
        # these are set as a side-effect of executing the query. Note that we calculate
        # separately a list of extra select columns needed for grammatical correctness
        # of the query, but these columns are not included in self.select.
        self.select = None
        self.annotation_col_map = None
        self.klass_info = None
        self.subquery = False

    def compile(self, node, select_format=False):
        return None

    def execute_sql(self, result_type=MULTI):
        self.setup_query()

    def results_iter(self, results=None):
        """
        Returns an iterator over the results from executing this query.
        """
        if self.query.model.__name__ == "ModelA":
            yield (13,)
            yield (14,)
            yield (15,)
        elif self.query.model.__name__ == "ModelB":
            yield (1, 13)
            yield (2, 14)

    def get_ressource_path(self, model, many=False):
        """
        return the ressource path relative to the base of the api.
        it use ressource_path and ressource_path_plurial, and fallback to the get_ressource_name()
        :param model: the model
        :param bool many: True if the ressource is for a many endpoint (list instead of details)
        :return:
        """
        if many:
            return getattr(model.APIMeta, 'ressource_path_plurial', None) or self.get_ressource_name(model, many)
        else:
            return getattr(model.APIMeta, 'ressource_path', None) or self.get_ressource_name(model, many)

    def get_ressource_name(self, model, many=False):
        """
        return the name of the ressource on the server
        if multi is True, it's the url for the «many» models, so we add a «s».
        the resulotion try first to check the APIMeta resource_name and resource_name_plural. if it don't exists,
        it will guess the value from the model name.(lower)
        :param model: the model
        :param bool many: if true, the url of many results
        :return:
        """
        if many:
            return getattr(model.APIMeta, 'resource_name_plural', None) or model.__name__.lower() + 's'
        else:
            return getattr(model.APIMeta, 'resource_name', None) or model.__name__.lower()


class SQLInsertCompiler(SQLCompiler):
    def execute_sql(self, return_id=False):
        query = self.query
        opts = query.get_meta()
        can_bulk = not return_id and self.connection.features.has_bulk_insert

        query_objs = query.objs
        if can_bulk:
            # bulk insert
                data = [
                    {
                        f.column: f.get_db_prep_save(
                            getattr(obj, f.attname) if self.query.raw else f.pre_save(obj, True),
                            connection=self.connection
                        )
                        for f in query.fields
                    }
                    for obj in query_objs
                ]

                json = {
                    self.get_ressource_name(query.model, many=True): data
                }
                response = self.connection.connection.post(
                    self.get_ressource_path(self.query.model, many=False),
                    json=json
                )
                if response.status_code != 201:
                    raise FakeDatabaseDbAPI2.ProgrammingError("error while creating %d %s.\n%s" %
                                                              (len(query_objs), opts.verbose_name, response.json()['errors']))
                result_json = response.json()
                for old, new in zip(query_objs, result_json[self.get_ressource_name(query.model, many=True)]):
                    setattr(old, opts.pk.attname, new[opts.pk.attname])
        else:
            for obj in query_objs:
                data = {
                    f.column: f.get_db_prep_save(
                        getattr(obj, f.attname) if self.query.raw else f.pre_save(obj, True),
                        connection=self.connection
                    )
                    for f in query.fields
                }

                json = {
                    self.get_ressource_name(query.model, many=False): data
                }
                response = self.connection.connection.post(
                    self.get_ressource_path(self.query.model, many=False),
                    json=json
                )
                if response.status_code != 201:
                    raise FakeDatabaseDbAPI2.ProgrammingError("error while creating %s.\n%s" % (obj, response.text))
                result = response.json()

            if return_id and result:
                return result[self.get_ressource_name(query.model, many=False)][opts.pk.column]


class SQLDeleteCompiler(SQLCompiler):
    pass


class SQLUpdateCompiler(SQLCompiler):
    pass


class SQLAggregateCompiler(SQLCompiler):
    pass
