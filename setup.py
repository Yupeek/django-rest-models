#!/usr/bin/env python

import os
import sys

import rest_models

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = rest_models.__VERSION__

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'testsettings'

if sys.argv[-1] == 'publish':
    # os.system('cd docs && make html')
    os.system('python setup.py sdist bdist_wheel')
    os.system('twine upload -r pypi dist/*')
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()

if sys.argv[-1] == 'doc':
    os.system('cd docs && make html')
    sys.exit()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme_file:
    readme = readme_file.read()

with open(os.path.join(os.path.dirname(__file__), 'test_requirements.txt')) as requirements_file:
    tests_require = requirements_file.readlines()

setup(
    name='django-rest-models',
    version=version,
    description="""django Fake ORM model that query an RestAPI instead of a database — """,
    long_description=readme,
    long_description_content_type='text/x-rst',
    author='Darius BERNARD',
    author_email='darius@yupeek.com',
    url='https://github.com/Yupeek/django-rest-models',
    tests_require=tests_require,
    install_requires=[
        'requests',
        'six',
        'Django<5.2',
        'unidecode',
    ],
    packages=[
        'rest_models',
        'rest_models.backend',
    ],
    include_package_data=True,
    license="BSD",
    zip_safe=False,
    keywords='django rest models API ORM',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
