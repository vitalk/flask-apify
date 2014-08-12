#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask.ext.apify.serializers.jsonp
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The JSON-P serializer for API response.

    :copyright: (c) by Vital Kudzelka.
"""
from flask import json
from flask import request
from flask import current_app
from werkzeug.local import LocalProxy

from . import Serializer


_apify = LocalProxy(lambda: current_app.extensions['apify'])


class JSONPSerializer(Serializer):
    """The JSON-P serializer.

    This serializer uses the previously registered JSON serializer to
    serialize data if exists, and fallback to default `json.dumps` otherwise.
    Then wraps the result with the name of the JSON-P callback function passed
    as parameter via request arguments (or does nothing if no callback
    function specified).

    :param callback_name: The name of the callback used as padding in output.
    """

    def __init__(self, callback_name='callback'):
        self.callback_name = callback_name

    def __call__(self, data):
        try:
            to_json = _apify.serializers['application/json']
        except KeyError:
            to_json = lambda x: json.dumps(x)

        callback = request.args.get(self.callback_name, False)
        return jsonp(to_json(data), callback)


def jsonp(json, padding=None):
    """Adds an optional padding to json string.

    >>> jsonp('{"ping": "pong"}', padding='console.log')
    'console.log({"ping": "pong"});'
    >>> jsonp('42')
    '42'

    :param json: The original json string.
    :param padding: An optional padding to wrap json string.
    """
    before = after = ''
    if padding:
        before = padding + '('
        after = ');'
    return before + json + after


to_javascript = JSONPSerializer()
