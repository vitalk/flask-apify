#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask.ext.apify.utils import key
from flask.ext.apify.utils import get_config
from flask.ext.apify.utils import self_config
from flask.ext.apify.utils import self_config_value
from flask.ext.apify.utils import unpack_response


def test_key():
    assert key('blueprint_name') == 'APIFY_BLUEPRINT_NAME'


def test_get_config():
    config = dict(a=1, b=2, c=3)
    config_with_prefix = {'_'.join(('apify', k)): v for k, v in config.items()}
    assert get_config(config_with_prefix, 'apify_') == config


def test_self_config(webapp):
    assert self_config(webapp) == {
        'APIDUMP_TEMPLATE': 'apidump.html',
        'DEFAULT_MIMETYPE': 'application/json',
    }


def test_self_config_value(webapp):
    assert self_config_value('apidump_template', webapp) == 'apidump.html'
    assert self_config_value('default_mimetype', webapp) == 'application/json'


def test_unpack_response():
    one, two, three = object(), object(), object()

    assert unpack_response(one) == (one, 200, {})
    assert unpack_response((one, two)) == (one, two, {})
    assert unpack_response((one, two, three)) == (one, two, three)
