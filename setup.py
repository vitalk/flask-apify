#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask-apify
    ~~~~~~~~~~~

    A Flask extension to create an API to your application as a ninja.

    :copyright: (c) by Vital Kudzelka
"""
from setuptools import setup


setup(
    name='flask-apify',
    version='0.5.1',
    license='MIT',
    author='Vital Kudzelka',
    author_email='vital.kudzelka@gmail.com',
    description='A Flask extension to create API to your application as a ninja',
    long_description=__doc__,
    packages=[
        'flaskext',
        'flaskext.apify'
    ],
    namespace_packages=['flaskext'],
    install_requires=['Flask'],
    tests_require=['pytest'],
    test_suite='pytest',
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
