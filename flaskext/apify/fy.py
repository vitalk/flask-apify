#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask.ext.apify.fy
    ~~~~~~~~~~~~~~~~~~

    The extension core.

    :copyright: (c) by Vital Kudzelka
"""
from functools import wraps
from itertools import chain

from flask import g
from flask import request
from flask import Response
from flask import Blueprint
from flask import current_app
from werkzeug.local import LocalProxy
from werkzeug.wrappers import Response as _Response
from werkzeug.datastructures import ImmutableDict

from .utils import key
from .utils import unpack_response
from .utils import self_config_value

from .exc import ApiError
from .exc import ApiNotAcceptable

from .serializers import DebugSerializer
from .serializers import JSONSerializer
from .serializers import get_serializer
from .serializers import get_default_serializer


default_config = ImmutableDict({
    # The default mimetype returned by API endpoints
    'default_mimetype': 'application/json',

    # The name of the jinja template rendered on debug view
    'apidump_template': 'apidump.html',
})


class Apify(object):
    """The Flask extension to create an API to your application as a ninja.

    :param app: Flask application instance
    :param blueprint_name: A name of the blueprint created, also uses to make a
        URLs via :func:`url_for` calls
    :param url_prefix: The url prefix to mount blueprint.
    :param preprocessor_funcs: A list of functions that should be called
        before a view callable.
    :param postprocessor_funcs: A list of functions that should be called
        after a view callable done but response object is not exists yet.
    :param finalizer_funcs: A list of functions that should be called after
        response object has been created.
    """

    # the serializer function per mimetype
    serializers = {
        'text/html': DebugSerializer(),
        'application/json': JSONSerializer(),
        'application/javascript': JSONSerializer(),
    }

    def __init__(self, app=None, blueprint_name='api', url_prefix=None,
                 preprocessor_funcs=None, postprocessor_funcs=None,
                 finalizer_funcs=None):

        # A list of functions that should decorate original view callable. To
        # register a function here, use the :meth:`preprocessor` decorator.
        self.preprocessor_funcs = list(chain((set_best_serializer,),
                                             preprocessor_funcs or ()))

        # A list of functions that should be called after original view
        # callable done but respone object is not yet exists. To register a
        # function here, use the :meth:`postprocessor` decorator.
        self.postprocessor_funcs = postprocessor_funcs or []

        # A list of functions that should be called after response object has
        # been created. To register a function here, use the :meth:`finalizer`
        # decorator.
        self.finalizer_funcs = finalizer_funcs or []

        self.blueprint = create_blueprint(blueprint_name, url_prefix)

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

        app.extensions = getattr(app, 'extensions', {})
        app.extensions['apify'] = self
        return self

    def route(self, rule, **options):
        """A decorator that is used to register a view function for a given URL
        rule, same as :meth:`route` in :class:`~flask.Blueprint` object.

        The passed view function decorates to catch all :class:`ApiError` errors
        to produce nice output on view errors.

        To allow apply decorator multiple times function will be decorated only
        if not previously decorated, e.g. has no attribute
        :attr:`is_api_method`.

        Example::

            @apify.route('/ping', defaults={'value': 200})
            @apify.route('/ping/<int:value>')
            def ping(value):
                pass

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
            if not hasattr(fn, 'is_api_method'):
                fn = catch_errors(ApiError)(fn)
                fn.is_api_method = True
            self.blueprint.add_url_rule(rule, view_func=fn, **options)
            return fn
        return wrapper

    def serializer(self, mimetype):
        """Register decorated function as serializer for specific mimetype.

        Serializer is a callable which accept one argument the raw data
        to process and returns serialized data::

            @apify.serializer('application/xml')
            def to_xml(data):
                '''Converts data to xml.'''
                return data

        :param mimetype: The mimetype to register function as a data serializer.
        :param fn: The serializer callable
        """
        def wrapper(fn):
            self.serializers[mimetype] = fn
            return fn
        return wrapper

    def preprocessor(self, fn):
        """Register a function to decorate original view function.

        :param fn: A view decorator

        Example::

            @apify.preprocessor
            def login_required(fn):
                raise ApiUnauthorized()

        """
        self.preprocessor_funcs.append(fn)
        return fn

    def postprocessor(self, fn):
        """Register a function as request postprocessor.

        :param fn: A request postprocessor function.

        Postprocessor function must carefully process incoming data, e.g view
        callable may returns optional status code and headers dictionary::

            @apify.postprocessor
            def modify_view_result(raw):
                raw, code, headers = unpack_response(raw)
                return raw, code, headers

        """
        self.postprocessor_funcs.append(fn)
        return fn

    def finalizer(self, fn):
        """Register a function to run after :class:`~flask.Response` object is
        created.

        :param fn: A function to register

        Each of finalizer function has access to result
        :class:`~flask.Response` object ready to return to endpoint user.
        For example, its possible to set custom headers to response::

            @apify.finalizer
            def set_custom_header(res):
                res.headers['X-Rate-Limit'] = 42

        """
        self.finalizer_funcs.append(fn)
        return fn


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
                # Call preprocessor functions
                func = apply_all(_apify.preprocessor_funcs, fn)

                # Call view callable
                raw = func(*args, **kwargs)

                # Call postprocessor functions
                raw = apply_all(_apify.postprocessor_funcs, raw)

                # Make a response object
                res = make_api_response(raw)

                # Finalize response
                return apply_all(_apify.finalizer_funcs, res)
            except errors as exc:
                return send_api_error(exc)
        return wrapper
    return decorator


def apply_all(funcs, arg):
    """Returns the result of applying function to arg.

    :param funcs: The list of functions to apply passed argument
    :param arg: The argument passed to each function recursively

    The result of:

        apply_all((one, two), arg)

    is equivalent to:

        one(two(arg))

    """
    for func in funcs:
        arg = func(arg)
    return arg


def create_blueprint(name, url_prefix):
    """Creates an API blueprint, but does not register it to any specific
    application.

    :param name: The blueprint name
    :param url_prefix: The url prefix to mount blueprint.
    """
    return Blueprint(name, __name__, url_prefix=url_prefix,
                     template_folder='templates')


def set_best_serializer(fn):
    """Set the best possible serializer and mimetype for response to the
    application globals according with the request accept header.

    Reraise on `ApiNotAcceptable` error.

    :param fn: A view function to decorate
    """
    try:
        g.api_mimetype, g.api_serializer = get_serializer(guess_best_mimetype())
    except ApiNotAcceptable as exc:
        g.api_mimetype, g.api_serializer = get_default_serializer()
        raise exc
    return fn


def guess_best_mimetype():
    """Returns the best mimetype that client may accept."""
    return request.accept_mimetypes.best


def make_api_response(raw):
    """Returns the valid response object.

    :param raw: The raw data to send
    """
    if isinstance(raw, _Response):
        return raw

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
    return make_api_response((raw, exc.code))


_apify = LocalProxy(lambda: current_app.extensions['apify'])
