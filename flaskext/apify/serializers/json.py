#!/usr/bin/env python
# encoding: utf-8
"""
    flask.ext.apify.serializers.json
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The JSON serializer for an API response.

    :copyright: (c) by Vital Kudzelka
"""
from flask import json

from . import Serializer


class JSONSerializer(Serializer):
    """The JSON serializer."""

    def __call__(self, raw):
        """Dumps data to JSON.

        :param raw: The raw data to process.
        """
        return json.dumps(raw)


to_json = JSONSerializer()
