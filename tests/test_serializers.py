#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask.ext.apify.serializers import Serializer
from flask.ext.apify.serializers import JSONSerializer
from flask.ext.apify.serializers import DebugSerializer


class TestSerializer(object):

    def setup(self):
        self.serializer = Serializer()

    def test_base_class_raises_not_implementent_error_on_call(self):
        with pytest.raises(NotImplementedError):
            self.serializer({})


class TestDebugSerializer(object):

    def setup(self):
        self.serializer = DebugSerializer()

    def test_dump(self, webapp):
        with webapp.test_request_context():
            assert self.serializer(42) == '<pre>42</pre>'


class TestJSONSerializer(object):

    def setup(self):
        self.serializer = JSONSerializer()

    def test_dump(self):
        assert self.serializer({'ping': 'pong'}) == '{"ping": "pong"}'
