#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from flask_apify import http


class TestHttpStatusCode:

    def test_is_server_error(self):
        assert not http.status.is_server_error(499)
        assert http.status.is_server_error(500)
        assert http.status.is_server_error(599)
        assert not http.status.is_server_error(600)
