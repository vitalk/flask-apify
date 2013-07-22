#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask.ext.apify.serializers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements serializers for an application API.

    :copyright: (c) by Vital Kudzelka
"""
from flask import current_app
from werkzeug.local import LocalProxy

from .json import to_json
from .debug import to_debug

from ..exc import ApiNotAcceptable
from ..utils import self_config
from ..utils import self_config_value


_apify = LocalProxy(lambda: current_app.extensions['apify'])


def get_serializer(mimetype):
    """Returns mimetype and serializer function to process response data.

    May raise `ApiNotAcceptable` error if cannot return serializer that can
    generate response in format accepted by client.

    :param mimetype: The response mimetype requested by client.
    """
    try:
        return mimetype, _apify.serializers[mimetype]
    except KeyError:
        raise ApiNotAcceptable()


def get_default_serializer():
    """Returns default serializer function and mimetype for response."""
    try:
        mimetype = self_config_value('default_mimetype')
        return mimetype, _apify.serializers[mimetype]
    except KeyError:
        raise RuntimeError(\
                'Serializer does not registered for mimetype '
                '"{}"'.format(mimetype))
