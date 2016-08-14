#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Flask-Apify
    ~~~~~~~~~~~

    A Flask extension to create an API to your application as a ninja.

    :copyright: (c) by Vital Kudzelka
"""
import io
import os
import re
import sys
from setuptools import (
    setup, find_packages
)
from setuptools.command.test import test


def read(*parts):
    """Reads the content of the file created from *parts*."""
    try:
        with io.open(os.path.join(*parts), 'r', encoding='utf-8') as f:
            return f.read()
    except IOError:
        return ''


def get_version():
    version_file = read('flask_apify', '__init__.py')
    version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]',
                              version_file, re.MULTILINE)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


class pytest(test):

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='Flask-Apify',
    version=get_version(),
    license='MIT',
    author='Vital Kudzelka',
    author_email='vital.kudzelka@gmail.com',
    url='https://github.com/vitalk/flask-apify',
    description='A Flask extension to create API to your application as a ninja',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    install_requires=['Flask'],
    tests_require=['pytest-flask', 'pytest'],
    test_suite='tests',
    cmdclass={
        'test': pytest
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
