#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask-apify
    ~~~~~~~~~~~

    A Flask extension to create an API to your application as a ninja.

    :copyright: (c) by Vital Kudzelka
"""
import io
import os
import re
import sys
from setuptools import setup
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
    name='flask-apify',
    version=get_version(),
    license='MIT',
    author='Vital Kudzelka',
    author_email='vital.kudzelka@gmail.com',
    description='A Flask extension to create API to your application as a ninja',
    long_description=__doc__,
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
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
