#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask_apify.utils
    ~~~~~~~~~~~~~~~~~

    The helper functions.

    :copyright: (c) by Vital Kudzelka
"""
from flask import current_app


key = lambda s: 'APIFY_{}'.format(s.upper())
"""Create config key for extension."""


def get_config(config, prefix):
    """Get config without annoying prefix.

    :param config: The original config dictionary
    :param prefix: The prefix to strip from keys of the original config
    """
    return {k.replace(prefix, ''): v for k, v in config.items()
            if k.startswith(prefix)}


self_config = lambda app: get_config(app.config, 'APIFY_')
"""The extension config without annoying prefix."""


def self_config_value(key, app=None):
    """Returns the config value for key.

    :param key: The key to lookup
    :param app: The Flask instance
    """
    app = app or current_app
    return self_config(app).get(key.upper())


def unpack_response(raw):
    """Unpack raw data from view function to (raw, code, headers) tuple. Fill in
    missed values.

    :param raw: The data returned by view function
    """
    if not isinstance(raw, tuple):
        return raw, 200, {}

    try:
        raw, code = raw
        return raw, code, {}
    except ValueError:
        pass

    try:
        raw, code, headers = raw
        return raw, code, headers
    except ValueError:
        pass

    return raw, 200, {}
