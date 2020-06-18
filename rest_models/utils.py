# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json
from collections import defaultdict

import six

try:
    from pathlib import Path
except ImportError:  # pragma: no cover
    class Path(object):
        """
        fake pathlib.Path for retro-compatiblitiy
        """
        def __init__(self, path):
            if isinstance(path, Path):
                path = path.path
            self.path = path

        def open(self, mode):
            return open(self.path, mode)


def dict_contains(subdict, maindict):
    """
    return True if the subdict is present with the sames values in dict.
    can be recursive. if maindict contains some key not in subdict it's ok.
    but if subdict has a key not in maindict or the value are not the same, it's a failure.

    >>> dict_contains(dict(a=1, b=2), dict(a=1, c=2, b=2))
    True

    >>> dict_contains(dict(a=dict(aa=1)), dict(a=dict(aa=1, bb=2), b=2))
    True

    >>> dict_contains(dict(a=dict(aa=1, bb=2)), dict(a=dict(aa=2)))
    False

    >>> dict_contains(dict(a=dict(aa=1)), dict(a=[]))
    False

    >>> dict_contains(dict(a=1), dict())
    False

    >>> dict_contains(dict(a=[1, 2, 3]), dict(a=[1, 2, 3]))
    True

    >>> dict_contains(dict(a=[1, 3, 2]), dict(a=[1, 2, 3]))
    False

    >>> dict_contains(dict(a=[1, 3]), dict(a=[1, 2, 3]))
    False

    >>> dict_contains(dict(a=[1, 3, 2]), dict(a={1, 2, 3}))
    True

    :param subdict: the smaller dict that should be present in the big one
    :param maindict: the dict
    :return: True if subdict is included in maindict
    :rtype: bool
    """
    try:
        for k, v in subdict.items():
            mainv = maindict[k]
            if isinstance(mainv, dict) and isinstance(v, dict):
                if not dict_contains(v, mainv):
                    return False
            elif isinstance(mainv, (set, frozenset)):
                return set(v) == mainv
            elif mainv != v:
                return False
    except KeyError:
        return False
    return True


class JsonFixtures(object):
    """
    a class that will take raw data or filenames to load api fixtures.
    it work with many usefull synthax.

    JsonFixtures(
        nested_json_fixtures,
        'path/to/fixtures.json',  # this fixture will contains the urls

        'model/url/'=[response...],
        'model_url': 'path/to/other/fixture.json  # this fixtures is a list of response
    )

    some variables can be injected in the urls::

    >>> f = JsonFixtures({'/model/%(pk)s/': ['hey']})
    >>> f['/model/134/'] # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    KeyError: ...'/model/134/'
    >>> f.set_variable({'pk': 134}) and None
    >>> f['/model/134/'] == ['hey']
    True

    >>> f = JsonFixtures({'/model': ['a'], 'b': 2}, c=3)
    >>> f.update({'d': 4, '/model': ['b']}, c=4)
    >>> f['/model'] == ['b', 'a']
    True
    >>> f['b']
    [2]
    >>> f['c']
    [4, 3]
    >>> f['d']
    [4]
    """

    def __init__(self, *args, **kwargs):
        self.files = []
        self.url_for_data = defaultdict(list)
        self.variable = {}
        self.update(*args, **kwargs)

    def update(self, *args, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, (list, tuple)):
                self.url_for_data[k][0:0] = list(v)
            else:
                self.url_for_data[k].insert(0, v)
        for file in args:
            if isinstance(file, (six.text_type, six.binary_type, Path)):
                self.files.append(file)
            elif isinstance(file, dict):
                self.update(**file)
            elif isinstance(file, JsonFixtures):
                self.update(**file._load())
            else:
                raise ValueError("%s is not supported as *args" % (type(file)))

    def set_variable(self, variable):
        """
        set the dict that will be used as variable for the url resolving
        :param variable:
        :return:
        """
        self.variable = variable
        return self

    def __load_json(self, path):
        """
        helper that load the json in path
        :param str|Path path: the path to load
        :return: the data loaded
        """
        try:
            with Path(path).open('r') as f:
                return json.load(f)
        except ValueError as ve:
            six.raise_from(ValueError("error while loading the fixture %s" % path), ve)

    def _load(self):
        """
        load the data from files and url_for_data and return the dict as expected by JsonFixtures
        :rtype: dict
        """
        res = {}
        for file in self.files:
            loaded = self.__load_json(file)
            for k, v in loaded.items():
                if isinstance(v, (list, tuple)):
                    res.setdefault(k, []).extend(v)
                else:
                    res.setdefault(k, []).append(v)

        for url, datas in self.url_for_data.items():
            if not isinstance(datas, (list, tuple)):
                datas = [datas]
            for data in datas:
                res.setdefault(url, [])
                if isinstance(data, Path):
                    data = self.__load_json(data)
                if isinstance(data, (list, tuple)):
                    res[url].extend(data)
                else:
                    res[url].append(data)
        return res

    def __getitem__(self, item):
        if not hasattr(self, "_loaded"):
            self._loaded = self._load()
        try:
            return self._loaded[item]
        except KeyError as ke:
            # try with varables
            for url, data in self._loaded.items():
                try:
                    if url % self.variable == item:
                        return data
                except KeyError:
                    # the resolving of url can use a %(name)s that is not in the dict
                    pass
            raise ke

    def items(self):
        if not hasattr(self, "_loaded"):
            self._loaded = self._load()
        for url, data in self._loaded.items():
            try:
                yield url % self.variable, data
            except KeyError:
                # the resolving of url can use a %(name)s that is not in the dict
                pass


def pgcd(a, b):
    """
    return the best page size for a given limited query

    :param a: the start offset
    :param b: the end offset
    :return:

    >>> pgcd(30, 40)
    10

    >>> pgcd(7, 13)
    1

    """
    while a % b != 0:
        a, b = b, a % b
    return b
