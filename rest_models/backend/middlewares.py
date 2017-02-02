# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging

logger = logging.getLogger(__name__)


class FakeApiResponse(object):
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    @property
    def text(self):
        try:
            return json.dumps(self.data)
        except TypeError:
            return repr(self.data)


class ApiMiddleware(object):
    """
    a base class to implemente a middleware that will
    interact with a api query/response
    """

    def process_request(self, params, requestid, connection):
        """
        process the request. if return other than None, it will be the result of the request

        :param dict params: the params given (and modified by previous middleware) for the _make_query.
                            the params can be updated at will by side-effect.
                    params contain
                        - verb: the verb to execut the request (post, get, put)
                        - url: the url in which the query will be executed
                        - data: the data given to the query to post,put, etc

        :param int requestid: the id of the current request done by this connection
        :param connection: the connection used for this query
        :return: the response if there is no need to pursue the query.
        """
        return None

    def process_response(self, params, response, requestid):
        """
        process the response from a previous query. MUST return a response (result)

        :param params: the params finaly given to query the api. same format as for process_request
        :param response:  the response, either the original one or modifier by preceding middleware
        :param int requestid: the id of the current request done by this connection
        :return:
        """
        return response

    @staticmethod
    def make_response(data, status_code):
        """
        helper to make a response (returned by process_response or process_request) with given data

        :param data: the data in the response (will be encoded in json to be compatible)
        :param status_code: the status code of the response
        :return: a FakeApiResponse that contains raw data
        """
        return FakeApiResponse(data, status_code)

    def empty_response(self):
        """
        shortcut to return a response with 204 status code and no data, which will be

        :return: a FakeApiResponse with no data and 204 status code
        """
        return self.make_response(data=None, status_code=204)

    def data_response(self, data, status_code=None):
        """
        shortcut to return a response with 200 and data

        :param data: the data to insert in the response
        :return: a FakeApiResponse with the given data
        """
        return self.make_response(data=data, status_code=status_code or 200)
