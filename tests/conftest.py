#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask import Flask
from flask.ext.apify import Apify


def create_app(config):
    apify = Apify()
    app = Flask(__name__)

    for key, value in config:
        app.config[key] = value

    apify.init_app(app)
    return app


@pytest.fixture
def webapp():
    return create_app({})


@pytest.fixture
def config(webapp):
    return webapp.config


@pytest.fixture
def client(webapp):
    return webapp.test_client()


@pytest.fixture
def apify(webapp):
    return webapp.extensions['apify']
