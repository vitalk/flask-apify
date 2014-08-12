#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask.ext.apify.serializers import Serializer


class TestSerializer(object):

    def setup(self):
        self.serializer = Serializer()

    def test_base_class_raises_not_implementent_error_on_call(self):
        with pytest.raises(NotImplementedError):
            self.serializer({})
