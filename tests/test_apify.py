#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import pytest
import logging

from flask import url_for
from flask_apify.fy import (
    catch_errors, guess_best_mimetype, set_best_serializer
)
from flask_apify.exc import (
    ApiError, ApiUnauthorized, ApiNotAcceptable
)
from flask_apify.serializers import (
    get_default_serializer, get_serializer, to_javascript, to_json, to_html
)

from .conftest import accept_mimetypes


PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
else:
    text_type = str


def b(s):
    return s.encode('utf-8') if isinstance(s, text_type) else s


def test_apify_init(app, apify):
    assert 'apify' in app.extensions
    assert apify.blueprint is not None
    assert apify.logger is logging.getLogger('flask-apify')
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


def test_apify_default_response_mimetype_is_application_javascript(app):
    mimetype, fn = get_default_serializer()
    assert mimetype == 'application/javascript'
    assert callable(fn)


def test_apify_get_default_serializer_may_raise_error_if_nosuch_serializer(app):
    app.config['APIFY_DEFAULT_MIMETYPE'] = 'nosuch/mimetype'

    with pytest.raises(RuntimeError):
        get_default_serializer()


def test_apify_call_require_explicit_mimetype(app, client):
    res = client.get(url_for('api.ping'))
    assert res.status_code == 406
    assert res.mimetype == 'application/javascript'


def test_apify_handle_custom_errors(client, accept_mimetypes):
    res = client.get(url_for('api.error'), headers=accept_mimetypes)
    assert res.status_code == 418
    assert b('This server is a teapot, not a coffee machine') in res.data


def test_apify_handle_http_exceptions(client, accept_mimetypes):
    res = client.get(url_for('api.forbidden'), headers=accept_mimetypes)
    assert res.status_code == 403
    assert b('the permission to access the requested resource') in res.data


def test_returns_server_error_if_exception_has_no_status_code(client, accept_mimetypes):
    res = client.get(url_for('api.bomb'), headers=accept_mimetypes)
    assert res.status_code == 500
    assert b('boom!') in res.data


def test_apify_allow_apply_route_decorator_multiple_times(app, client, accept_json):
    res = client.get(url_for('api.ping'), headers=accept_json)
    assert res.status_code == 200
    assert res.json == {'value': 200}

    res = client.get(url_for('api.ping', value=404), headers=accept_json)
    assert res.status_code == 200
    assert res.json == {'value': 404}


@pytest.fixture
def stdout():
    import sys
    if sys.version_info[0] == 2:
        from cStringIO import StringIO
    else:
        from io import StringIO

    return StringIO()


@pytest.fixture
def app_logger(apify, stdout):
    apify.logger.level = logging.ERROR
    apify.logger.addHandler(logging.StreamHandler(stdout))


@pytest.mark.usefixtures('app_logger')
class TestLogging(object):

    def test_log_exception(self, app, apify, stdout):
        with app.test_request_context('/foo'):
            try:
                1 // 0
            except ZeroDivisionError as exc:
                apify.log_exception(exc)
                err = stdout.getvalue()

                # Request path and method
                assert 'Exception on GET /foo' in err
                # Exception traceback
                assert 'Traceback (most recent call last):' in err
                # Erroneous expression
                assert '1 // 0' in err
                # Exception itself
                assert 'ZeroDivisionError:' in err

    def test_http_exception_logging(self, apify, client, stdout, accept_any):
        apify.logger.level = logging.INFO
        client.get(url_for('api.forbidden'), headers=accept_any)

        err = stdout.getvalue()
        assert 'Exception on GET /forbidden' in err
        assert '403: Forbidden' in err

    def test_exception_logging(self, client, stdout, accept_any):
        res = client.get(url_for('api.bomb'), headers=accept_any)

        err = stdout.getvalue()
        assert 'Exception on GET /bomb' in err
        assert 'Bomb:' in err


class TestCatchErrorsDecorator(object):

    def test_catch_error(self):
        @catch_errors(ValueError, errorhandler=lambda x: x)
        def raise_error(value):
            raise ValueError

        assert raise_error('What is the meaning of the Life?')

    def test_may_catch_multiple_errors(self):
        @catch_errors((ValueError, ZeroDivisionError), lambda x: x)
        def raise_error(value):
            if value == 0:
                raise ZeroDivisionError
            raise ValueError

        assert raise_error(0)
        assert raise_error(42)

    def test_exec_errorhandler(self):
        @catch_errors(ValueError, errorhandler=lambda x: 42)
        def raise_error(value):
            raise ValueError

        assert raise_error('What is the meaning of the Life?') == 42


class TestMimetypeDetection(object):

    def test_support_wildcards(self, app, accept_any):
        with app.test_request_context(headers=accept_any):
            assert guess_best_mimetype() == 'application/javascript'

    @pytest.mark.options(apify_default_mimetype='text/xml')
    def test_returns_default_mimetype_if_client_may_accept_any_mimetype(self, app, accept_any):
        with app.test_request_context(headers=accept_any):
            assert guess_best_mimetype() == 'text/xml'

    @pytest.mark.options(apify_default_mimetype='application/xml')
    def test_wildcard_in_subtype(self, app):
        accept_headers = accept_mimetypes('application/*; q=0.1,'
                                          'application/json; q=1,'
                                          'application/javascript')
        with app.test_request_context(headers=accept_headers):
            assert guess_best_mimetype() == 'application/xml'

    def test_select_mimetype_with_better_quality_when_multiple_choices(self, app):
        accept_headers = accept_mimetypes('application/javascript; q=0.9,'
                                          'application/json; q=1')
        with app.test_request_context(headers=accept_headers):
            assert guess_best_mimetype() == 'application/json'

    def test_invalid_accept_header(self, app):
        with app.test_request_context(headers=accept_mimetypes('*/json')):
            assert guess_best_mimetype() is None

    def test_not_acceptable_mimetype(self, app):
        with app.test_request_context(headers=accept_mimetypes('text/xml')):
            assert guess_best_mimetype() is None

    def test_respect_available_mimetypes(self, app, apify):
        @apify.serializer('text/xml')
        def to_xml(x):
            return x

        with app.test_request_context(headers=accept_mimetypes('text/xml')):
            assert guess_best_mimetype() == 'text/xml'


def test_apify_add_preprocessor(apify):
    @apify.preprocessor
    def my_preprocessor():
        pass

    assert my_preprocessor in apify.preprocessor_funcs


def test_default_function_argument_in_preprocessor(apify):
    @apify.preprocessor()
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
    assert res.status_code == 401
    assert b('The server could not verify that you are '
             'authorized to access the requested URL.') in res.data


def test_view_callable_may_rewrite_response_object(client, accept_mimetypes):
    res = client.get(url_for('api.rewrite_response'), headers=accept_mimetypes)
    assert res.mimetype == 'custom/mimetype'
    assert res.data == b('response has been rewritten')


def test_preprocessor_may_rewrite_view_response(app, apify, client, accept_mimetypes):
    @apify.preprocessor
    def rewrite_response(fn):
        def wrapper():
            return app.response_class('response has been rewritten',
                                      mimetype='custom/mimetype')
        return wrapper

    res = client.get(url_for('api.ping'), headers=accept_mimetypes)
    assert res.mimetype == 'custom/mimetype'
    assert res.data == b('response has been rewritten')


def test_apify_register_postprocessor(apify):
    @apify.postprocessor
    def my_postprocessor():
        pass

    assert my_postprocessor in apify.postprocessor_funcs


def test_default_function_argument_in_postprocessor(apify):
    @apify.postprocessor()
    def my_postprocessor():
        pass

    assert my_postprocessor in apify.postprocessor_funcs


def test_apify_exec_postprocessor(apify, client, accept_json):
    @apify.postprocessor
    def attach_something(raw):
        raw.update(something=42)
        return raw

    res = client.get(url_for('api.ping'), headers=accept_json)
    assert res.status_code == 200
    assert res.json == {'something': 42, 'value': 200}


def test_apify_add_finalizer(apify):
    @apify.finalizer
    def teardown():
        pass

    assert teardown in apify.finalizer_funcs


def test_default_function_argument_in_finalizer(apify):
    @apify.finalizer()
    def teardown():
        pass

    assert teardown in apify.finalizer_funcs


def test_apify_exec_finalizer(apify, client, accept_mimetypes):
    @apify.finalizer
    def set_custom_header(res):
        res.headers['X-Rate-Limit'] = 42
        return res

    res = client.get(url_for('api.ping'), headers=accept_mimetypes)
    assert res.status_code == 200
    assert res.headers['X-Rate-Limit'] == '42'


def test_apify_can_handle_finalizer_error(apify, client, accept_mimetypes):
    class ImATeapot(ApiError):
        code = 418

    @apify.finalizer
    def raise_error(res):
        raise ImATeapot('Server too hot. Try it later.')

    res = client.get(url_for('api.ping'), headers=accept_mimetypes)
    assert res.status_code == 418
    assert b('Server too hot. Try it later.') in res.data
