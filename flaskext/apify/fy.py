#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask.ext.apify.fy
    ~~~~~~~~~~~~~~~~~~

    The extension core.

    :copyright: (c) by Vital Kudzelka
"""
from functools import wraps

from flask import g
from flask import request
from flask import Response
from flask import Blueprint
from werkzeug.datastructures import ImmutableDict

from .utils import key
from .utils import unpack_response
from .utils import self_config_value

from .exc import ApiError
from .exc import ApiNotAcceptable

from .serializers import to_json
from .serializers import to_debug
from .serializers import get_serializer
from .serializers import get_default_serializer


default_config = ImmutableDict({
    # The name of the blueprint to register API endpoints
    'blueprint_name': 'api',

    # The default mimetype returned by API endpoints
    'default_mimetype': 'application/json',

    # The name of the jinja template rendered on debug view
    'apidump_template': 'apidump.html',
})


class Apify(object):
    """The Flask extension to create an API to your application as a ninja.

    :param app: Flask application instance
    :param url_prefix: The url prefix to mount blueprint.
    """

    # the serializer function per mimetype
    serializers = {
        'text/html': to_debug,
        'application/json': to_json,
        'application/javascript': to_json,
    }

    def __init__(self, app=None, url_prefix=None):
        self.url_prefix = url_prefix
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize an application to use with extension.

        :param app: The Flask instance

        Example::

            from flask import Flask
            from flask.ext.apify import Apify

            app = Flask(__name__)
            apify = Apify()
            apify.init_app(app)

        """
        self.app = app

        for k, v in default_config.iteritems():
            app.config.setdefault(key(k), v)

        self.blueprint = create_blueprint(self_config_value('blueprint_name', app),
                                          self.url_prefix)

        app.extensions = getattr(app, 'extensions', {})
        app.extensions['apify'] = self
        return self

    def register_routes(self):
        """Register all routes created by extension to an application.

        You MUST call this method after registration ALL view functions.

        Example::

            apify.route('/todos')(lambda: 'todos')
            apify.route('/todos/<int:todo_id>')(lambda x: 'todo %s' % x)

            # later
            apify.register_routes()

        """
        self.app.register_blueprint(self.blueprint)

    def route(self, rule, **options):
        """A decorator that is used to register a view function for a given URL
        rule, same as :meth:`route` in :class:`~flask.Blueprint` object.

        The passed view function decorates to catch all :class:`ApiError` errors
        to produce nice output on view errors.

        :param rule: The URL rule string
        :param options: The options to be forwarded to the
            underlying :class:`~werkzeug.routing.Rule` object.

        Example::

            @apify.route('/todos/<int:todo_id>', methods=('DELETE'))
            def rmtodo(todo_id):
                '''Remove todo.'''
                pass

        """
        def wrapper(fn):
            fn = catch_errors(ApiError)(fn)
            self.blueprint.add_url_rule(rule, view_func=fn, **options)
            return fn
        return wrapper

    def serializer(self, mimetype):
        """Register decorated function as serializer for specific mimetype.

        :param mimetype: The mimetype to register function as a data serializer.
        :param fn: The serializers function

        Example::

            @apify.serializer('application/xml')
            def to_xml(data):
                '''Converts data to xml.'''
                pass

        """
        def wrapper(fn):
            self.serializers[mimetype] = fn
            return fn
        return wrapper


def catch_errors(*errors):
    """The decorator to catch errors raised inside the decorated function.

    Uses in :meth:`route` of :class:`Apify` object to produce nice output for
    view errors and exceptions.

    :param errors: The errors to catch up
    :param fn: The view function to decorate

    Example::

        @catch_errors(ApiError)
        def may_raise_error():
            raise ApiError('Too busy. Try later.')

    """
    def decorator(fn):
        assert errors, 'Some dumbas forgot to specify errors to catch?'
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                preprocess_api_response()
                return send_api_response(fn(*args, **kwargs))
            except errors as exc:
                return send_api_error(exc)
        return wrapper
    return decorator


def create_blueprint(name, url_prefix):
    """Creates an API blueprint, but does not register it to any specific
    application.

    :param name: The blueprint name
    :param url_prefix: The url prefix to mount blueprint.
    """
    return Blueprint(name, __name__, url_prefix=url_prefix,
                     template_folder='templates')


def preprocess_api_response():
    """Preprocess response.

    Set the best possible serializer and mimetype for response to the
    application globals according with the request accept header.

    Reraise on `ApiNotAcceptable` error.
    """
    try:
        g.api_mimetype, g.api_serializer = get_serializer(guess_best_mimetype())
    except ApiNotAcceptable as exc:
        g.api_mimetype, g.api_serializer = get_default_serializer()
        raise exc


def guess_best_mimetype():
    """Returns the best mimetype that client may accept."""
    return request.accept_mimetypes.best


def send_api_response(raw):
    """Returns the valid response object.

    :param raw: The raw data to send
    """
    raw, code, headers = unpack_response(raw)

    res = Response(g.api_serializer(raw), headers=headers, mimetype=g.api_mimetype)
    res.status_code = code
    return res


def send_api_error(exc):
    """Returns the API error wrapped in response object.

    :param exc: The exception raised
    """
    raw = {
        'error': exc.name,
        'message': exc.description,
    }
    return send_api_response((raw, exc.code))
