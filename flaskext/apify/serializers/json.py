#!/usr/bin/env python
# encoding: utf-8
"""
    flask.ext.apify.serializers.json
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The JSON serializer for an API response.

    :copyright: (c) by Vital Kudzelka
"""
from flask import json


to_json = lambda x: json.dumps(x)
"""The JSON serializer."""
