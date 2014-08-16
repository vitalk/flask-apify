#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask.ext.apify.serializers import Serializer
from flask.ext.apify.serializers.debug import DebugSerializer
from flask.ext.apify.serializers.json import JSONSerializer
from flask.ext.apify.serializers.jsonp import JSONPSerializer
from flask.ext.apify.serializers.jsonp import jsonp


class TestSerializer(object):

    def setup(self):
        self.serializer = Serializer()

    def test_base_class_raises_not_implementent_error_on_call(self):
        with pytest.raises(NotImplementedError):
            self.serializer({})


class TestDebugSerializer(object):

    def setup(self):
        self.serializer = DebugSerializer()

    def test_dump(self, app):
        assert self.serializer(42) == '<pre>42</pre>'


class TestJSONSerializer(object):

    def setup(self):
        self.serializer = JSONSerializer()

    def test_dump(self):
        assert self.serializer({'ping': 'pong'}) == '{"ping": "pong"}'


class TestJSONPSerializer(object):

    def setup(self):
        self.serializer = JSONPSerializer()

    def test_add_padding_to_string(self):
        assert jsonp('{"ping": "pong"}', 'console.log') == \
                'console.log({"ping": "pong"});'

    def test_returns_string_as_is_if_no_padding(self):
        assert jsonp('hello') == 'hello'

    def test_use_previously_registered_serializer_to_dump_json(self, app, apify):
        @apify.serializer('application/json')
        def my_json(raw):
            return '42'

        assert self.serializer('What is the meaning of the Life?') == '42'

    def test_use_callback_function_from_request_arguments_to_wrap_output(self, app):
        with app.test_request_context('?callback=console.log'):
            assert self.serializer('42') == 'console.log(42);'

    def test_support_custom_callback_name(self, app):
        serializer = JSONPSerializer(callback_name='jsonp')
        with app.test_request_context('?jsonp=console.log'):
            assert serializer('42') == 'console.log(42);'
