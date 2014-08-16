#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask import url_for
from flask.ext.apify.fy import set_best_serializer
from flask.ext.apify.exc import ApiError
from flask.ext.apify.exc import ApiUnauthorized
from flask.ext.apify.exc import ApiNotAcceptable
from flask.ext.apify.serializers import get_default_serializer
from flask.ext.apify.serializers import get_serializer
from flask.ext.apify.serializers import to_javascript
from flask.ext.apify.serializers import to_json
from flask.ext.apify.serializers import to_html


def test_apify_init(app, apify):
    assert 'apify' in app.extensions
    assert apify.blueprint is not None
    assert apify.preprocessor_funcs == [set_best_serializer,]
    assert apify.postprocessor_funcs == []
    assert apify.finalizer_funcs == []
    assert apify.serializers['text/html'] is to_html
    assert apify.serializers['application/json'] is to_json
    assert apify.serializers['application/javascript'] is to_javascript
    assert apify.serializers['application/json-p'] is to_javascript
    assert apify.serializers['text/json-p'] is to_javascript


def test_apify_does_not_require_app_object_while_instantiated(client, accept_mimetypes):
    res = client.get(url_for('api.ping'), headers=accept_mimetypes)
    assert res.status_code == 200


def test_apify_register_serializer_for_mimetype(app, apify):
    @apify.serializer('application/xml')
    def to_xml(x):
        return x

    mimetype, serializer = get_serializer('application/xml')
    assert mimetype == 'application/xml'
    assert serializer is to_xml


def test_apify_get_serializer(app, mimetype):
    mime, fn = get_serializer(mimetype)
    assert mime == mimetype
    assert callable(fn)


def test_apify_get_serializer_may_raise_error(app):
    with pytest.raises(ApiNotAcceptable):
        get_serializer('nosuch/mimetype')


def test_apify_default_response_mimetype_is_application_json(app):
    mimetype, fn = get_default_serializer()
    assert mimetype == 'application/json'
    assert callable(fn)


def test_apify_get_default_serializer_may_raise_error_if_nosuch_serializer(app):
    app.config['APIFY_DEFAULT_MIMETYPE'] = 'nosuch/mimetype'

    with pytest.raises(RuntimeError):
        get_default_serializer()


def test_apify_call_require_explicit_mimetype(app, client):
    res = client.get(url_for('api.ping'))
    assert res.status == '406 NOT ACCEPTABLE'
    assert res.mimetype == 'application/json'


def test_apify_handle_custom_errors(client, accept_mimetypes):
    res = client.get(url_for('api.error'), headers=accept_mimetypes)
    assert res.status_code == 418
    assert 'This server is a teapot, not a coffee machine' in res.data


def test_apify_allow_apply_route_decorator_multiple_times(app, client, accept_json):
    res = client.get(url_for('api.ping'), headers=accept_json)
    assert res.status == '200 OK'
    assert '{"value": 200}' == res.data

    res = client.get(url_for('api.ping', value=404), headers=accept_json)
    assert res.status == '200 OK'
    assert '{"value": 404}' == res.data


def test_apify_add_preprocessor(apify):
    @apify.preprocessor
    def my_preprocessor():
        pass

    assert my_preprocessor in apify.preprocessor_funcs


def test_apify_add_function_to_set_best_serializer_as_default_preprocessor(apify):
    assert set_best_serializer in apify.preprocessor_funcs


def test_apify_exec_preprocessors(apify, client, accept_mimetypes):
    @apify.preprocessor
    def login_required(fn):
        raise ApiUnauthorized()

    res = client.get(url_for('api.ping'), headers=accept_mimetypes)
    assert res.status == '401 UNAUTHORIZED'
    assert "The server could not verify that you are authorized to access the requested URL." in res.data


def test_preprocessor_may_rewrite_view_response(app, apify, client, accept_mimetypes):
    @apify.preprocessor
    def rewrite_response(fn):
        def wrapper():
            return app.response_class('response has been rewritten',
                                      mimetype='custom/mimetype')
        return wrapper

    res = client.get(url_for('api.ping'), headers=accept_mimetypes)
    assert res.mimetype == 'custom/mimetype'
    assert 'response has been rewritten' == res.data


def test_apify_register_postprocessor(apify):
    @apify.postprocessor
    def my_postprocessor():
        pass

    assert my_postprocessor in apify.postprocessor_funcs


def test_apify_exec_postprocessor(apify, client, accept_json):
    @apify.postprocessor
    def attach_something(raw):
        raw.update(something=42)
        return raw

    res = client.get(url_for('api.ping'), headers=accept_json)
    assert res.status == '200 OK'
    assert res.data == '{"something": 42, "value": 200}'


def test_apify_add_finalizer(apify):
    @apify.finalizer
    def teardown():
        pass

    assert teardown in apify.finalizer_funcs


def test_apify_exec_finalizer(apify, client, accept_mimetypes):
    @apify.finalizer
    def set_custom_header(res):
        res.headers['X-Rate-Limit'] = 42
        return res

    res = client.get(url_for('api.ping'), headers=accept_mimetypes)
    assert res.status == '200 OK'
    assert res.headers['X-Rate-Limit'] == '42'


def test_apify_can_handle_finalizer_error(apify, client, accept_mimetypes):
    class ImATeapot(ApiError):
        code = 418

    @apify.finalizer
    def raise_error(res):
        raise ImATeapot('Server too hot. Try it later.')

    res = client.get(url_for('api.ping'), headers=accept_mimetypes)
    assert res.status == '418 I\'M A TEAPOT'
    assert 'Server too hot. Try it later.' in res.data
