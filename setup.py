#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest

import rest_models

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = rest_models.__VERSION__

if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'testsettings'

if sys.argv[-1] == 'publish':
    os.system('cd docs && make html')
    os.system('python setup.py sdist bdist_wheel upload')
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()

if sys.argv[-1] == 'doc':
    os.system('cd docs && make html')
    sys.exit()

with open('README.rst') as readme_file:
    readme = readme_file.read()


def project_test_suite():

    test_suite = unittest.defaultTestLoader.discover('testapp', top_level_dir='.')
    test_suite.addTest(unittest.defaultTestLoader.discover('rest_models', top_level_dir='.'))

    return test_suite

setup(
    name='django-rest-models',
    version=version,
    description="""django Fake ORM model that query an RestAPI instead of a database — """,
    long_description=readme,
    author='Darius BERNARD',
    author_email='darius@yupeek.com',
    url='https://github.com/Yupeek/django-rest-models',
    test_suite="__main__.project_test_suite",
    packages=[
        'rest_models',
    ],
    include_package_data=True,
    install_requires=[
    ],
    license="GNU GENERAL PUBLIC LICENSE",
    zip_safe=False,
    keywords='django rest models API ORM',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
