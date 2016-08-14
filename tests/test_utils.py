#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask_apify.utils import (
    key, get_config, self_config, self_config_value, unpack_response
)


def test_key():
    assert key('blueprint_name') == 'APIFY_BLUEPRINT_NAME'


def test_get_config():
    config = dict(a=1, b=2, c=3)
    config_with_prefix = {'_'.join(('apify', k)): v for k, v in config.items()}
    assert get_config(config_with_prefix, 'apify_') == config


def test_self_config(app):
    assert self_config(app) == {
        'APIDUMP_TEMPLATE': 'apidump.html',
        'DEFAULT_MIMETYPE': 'application/javascript',
    }


def test_self_config_value(app):
    assert self_config_value('apidump_template', app) == 'apidump.html'
    assert self_config_value('default_mimetype', app) == 'application/javascript'


def test_unpack_response():
    one, two, three = object(), object(), object()

    assert unpack_response(one) == (one, 200, {})
    assert unpack_response((one, two)) == (one, two, {})
    assert unpack_response((one, two, three)) == (one, two, three)
