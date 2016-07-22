#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask_apify.http
    ~~~~~~~~~~~~~~~~

    Contains utilities to work with HTTP status codes.

    :copyright: (c) by Vital Kudzelka
    :license: MIT
"""


class status(object):
    """Contains descriptive functions to work with HTTP status codes."""

    @staticmethod
    def is_server_error(code):
        return 500 <= code <= 599
