#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask import abort
from flask import Flask
from flask.ext.apify import Apify
from flask.ext.apify.exc import ApiError


def create_app(**options):
    app = Flask(__name__, template_folder='../flaskext/apify/templates')

    for key, value in options.items():
        app.config[key.upper()] = value

    return app


@pytest.fixture
def app(request):
    """Use `pytest.mark.app` decorator to pass options to your application
    factory::

        @pytest.mark.app(apify_default_mimetype='text/xml')
        def test_something(app):
            pass

    During tests execution application has pushed context, e.g. `url_for`,
    `session`, etc. can be used in tests as is::

        def test_app(app, client):
            assert client.get(url_for('view')).status_code == 200

    """
    app = create_app()
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

    @apify.route('/forbidden')
    def forbidden():
        abort(403)

    @apify.route('/bomb')
    def bomb():
        class Bomb(ApiError):
            description = "boom!"

        raise Bomb()

    @apify.route('/rewrite_response')
    def rewrite_response():
        return app.response_class('response has been rewritten',
                                  mimetype='custom/mimetype')

    apify.init_app(app)
    app.register_blueprint(apify.blueprint)

    return app


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
