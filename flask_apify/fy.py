#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask_apify.fy
    ~~~~~~~~~~~~~~

    The extension core.

    :copyright: (c) by Vital Kudzelka
"""
import logging
from functools import wraps
from itertools import chain

from flask import (
    current_app, g, request, Blueprint
)
from werkzeug.local import LocalProxy
from werkzeug.datastructures import ImmutableDict

from . import http
from .utils import (
    key, unpack_response, self_config_value
)
from .exc import (
    ApiError, ApiNotAcceptable, HTTPException
)
from .serializers import (
    get_default_serializer, get_serializer, to_javascript, to_json, to_html
)


default_config = ImmutableDict({
    # The default mimetype returned by API endpoints
    'default_mimetype': 'application/javascript',

    # The name of the jinja template rendered on debug view
    'apidump_template': 'apidump.html',
})


class Apify(object):
    """The Flask extension to create an API to your application as a ninja.

    Extension has a :attr:`logger` instance to log errors or exceptions
    occurred during request dispatching. That logger is by default not
    configured with an any handler. You can easy add your own handler to
    obtain log messages emitted by extension::

        api = Apify(app)
        api.logger.addHandler(StreamHandler())

    Or reuse the handlers from your application::

        app = Flask(__name__)
        api = Apify(app)
        for handler in app.logger.handlers:
            api.logger.addHandler(handler)

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
        'text/html': to_html,
        'application/json': to_json,
        'application/javascript': to_javascript,
        'application/json-p': to_javascript,
        'text/json-p': to_javascript,
    }

    def __init__(self, app=None, blueprint_name='api', url_prefix=None,
                 preprocessor_funcs=None, postprocessor_funcs=None,
                 finalizer_funcs=None):
        self.app = app

        # A logger instance uses to log errors and exceptions occurred during
        # request dispatching.
        self.logger = logging.getLogger('flask-apify')
        class NullHandler(logging.StreamHandler):
            def emit(*_):
                pass
        self.logger.addHandler(NullHandler())

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
            from flask_apify import Apify

            app = Flask(__name__)
            apify = Apify()
            apify.init_app(app)

        """
        for k, v in default_config.items():
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
                fn = self.dispatch_api_request(fn)
                fn.is_api_method = True
            self.blueprint.add_url_rule(rule, view_func=fn, **options)
            return fn
        return wrapper

    def dispatch_api_request(self, fn):
        """Decorator uses to create a function which does the request
        dispatching. On top of that performs request pre and postprocessing
        as well as exception catching and error handling.

        :param fn: The view callable.
        """
        @wraps(fn)
        @catch_errors(HTTPException, errorhandler=self.handle_http_exception)
        @catch_errors(ApiError, errorhandler=self.handle_api_exception)
        def wrapper(*args, **kwargs):
            # Call preprocessor functions
            func = apply_all(self.preprocessor_funcs, fn)

            # Call view callable
            raw = func(*args, **kwargs)

            # Call postprocessor functions
            raw = apply_all(self.postprocessor_funcs, raw)

            # Make a response object
            res = self.make_api_response(raw)

            # Finalize response
            res = apply_all(self.finalizer_funcs, res)

            return res
        return wrapper

    def make_api_response(self, raw):
        """Creates the response object from value returned by a view callable.

        The `raw` may be a tuple in the form ``(raw, status_code, headers)``
        or ``(raw, status_code)``.

        :param raw: The raw data from view callable.
        """
        response_class = current_app.response_class

        # If view function or postprocessor creates a valid response object
        # then no need to create it again, just return what we've got.
        if isinstance(raw, response_class):
            return raw

        payload, code, headers = unpack_response(raw)
        payload, mimetype = g.api_serializer(payload), g.api_mimetype

        res = response_class(payload, headers=headers, mimetype=mimetype)
        res.status_code = code
        return res

    def handle_api_exception(self, exc):
        """Handles an API exception. By default this returns the exception as
        response object.

        :param exc: The exception raised
        """
        # Force set status code of the exception to 500 if exception
        # does not provides that value explicitly. This also set exception
        # name to more useful value, e.g. "Internal Server Error"
        # instead of "Unknown Error".
        status_code = exc.code
        if status_code is None:
            exc.code = status_code = 500

        payload = {
            'error': exc.name,
            'message': exc.description,
        }

        self.log_exception(exc)
        return self.make_api_response((payload, status_code))

    handle_http_exception = handle_api_exception
    """Handles an HTTP exception. Alias to :meth:`handle_api_exception`."""

    def log_exception(self, exc_info):
        """Logs an exception to the configured :attr:`logger` instance.
        If exception is a server error or does not contain status code
        explicitly, then the exception logged as error and as info otherwise.

        :param exc_info: The exception to log.
        """
        status_code = getattr(exc_info, 'code', 500)
        if http.status.is_server_error(status_code):
            logger_func = self.logger.error
        else:
            logger_func = self.logger.info

        logger_func('Exception on %s %s' % (
            request.method,
            request.path
        ), exc_info=exc_info)

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

    def preprocessor(self, fn=None):
        """Register a function to decorate original view function.

        :param fn: A view decorator

        Example::

            @apify.preprocessor
            def login_required(fn):
                raise ApiUnauthorized()

        """
        def decorator(fn):
            self.preprocessor_funcs.append(fn)
            return fn
        if fn is None:
            return decorator
        return decorator(fn)

    def postprocessor(self, fn=None):
        """Register a function as request postprocessor.

        :param fn: A request postprocessor function.

        Postprocessor function must carefully process incoming data, e.g view
        callable may returns optional status code and headers dictionary::

            @apify.postprocessor
            def modify_view_result(raw):
                raw, code, headers = unpack_response(raw)
                return raw, code, headers

        """
        def decorator(fn):
            self.postprocessor_funcs.append(fn)
            return fn
        if fn is None:
            return decorator
        return decorator(fn)

    def finalizer(self, fn=None):
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
        def decorator(fn):
            self.finalizer_funcs.append(fn)
            return fn
        if fn is None:
            return decorator
        return decorator(fn)


def catch_errors(errors, errorhandler):
    """The decorator to catch errors raised inside the decorated function and
    pass them to specified error handler.

    Uses in :meth:`route` of :class:`Apify` object to produce nice output for
    view errors and exceptions.

    :param errors: The errors to catch up
    :param errorhandler: The function which handles the error if occurs
    :param fn: The view function to decorate

    Example::

        @catch_errors(ApiError, errorhandler=reraise)
        def may_raise_error():
            raise ApiError('Too busy. Try later.')

    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except errors as exc:
                return errorhandler(exc)
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
    """Returns the best mimetype that client may accept. If client may receive
    any mimetype then returns the default one.
    """
    def _normalize(x):
        x = x.lower()
        return ('*', '*') if x == '*' else x.split('/', 1)

    def_mimetype = self_config_value('default_mimetype')
    def_type, def_subtype = _normalize(def_mimetype)

    for value in request.accept_mimetypes.values():
        value_type, value_subtype = _normalize(value)
        if (value_type == value_subtype == '*') or \
           (value_type == def_type and value_subtype == '*' ):
            return def_mimetype

    return request.accept_mimetypes.best_match(_apify.serializers.keys())


_apify = LocalProxy(lambda: current_app.extensions['apify'])
