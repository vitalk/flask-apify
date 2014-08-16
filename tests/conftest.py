#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask import Flask
from flask.ext.apify import Apify
from flask.ext.apify.exc import ApiError


def create_app(config):
    app = Flask(__name__, template_folder='../flaskext/apify/templates')

    for key, value in config:
        app.config[key] = value

    return app


@pytest.fixture
def app(request):
    """During tests execution application has pushed context, e.g. `url_for`,
    `session`, etc. can be used in tests as is::

        def test_app(app, client):
            assert client.get(url_for('view')).status_code == 200

    """
    app = create_app({})
    apify = Apify()

    @apify.route('/ping')
    @apify.route('/ping/<int:value>')
    def ping(value=200):
        return {'value': value}

    @apify.route('/error')
    def error():
        class ImATeapot(ApiError):
            code = 418
            description = 'This server is a teapot, not a coffee machine'

        raise ImATeapot

    apify.init_app(app)
    app.register_blueprint(apify.blueprint)

    ctx = app.test_request_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture
def config(app):
    return app.config


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def apify(app):
    return app.extensions['apify']


@pytest.fixture(params=['application/json', 'application/javascript',
                        'application/json-p', 'text/json-p', 'text/html'])
def mimetype(request):
    return request.param


@pytest.fixture
def accept_mimetypes(mimetype):
    return [('Accept', mimetype)]


@pytest.fixture(params=['application/json', 'application/javascript',
                        'application/json-p', 'text/json-p'])
def accept_json(request):
    return accept_mimetypes(request.param)
