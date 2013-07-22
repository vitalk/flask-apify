#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask.ext.serializers.debug
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The debug serializer uses to dump response into the HTML page to inspect in
    the browser.

    :copyright: (c) by Vital Kudzelka
"""
from flask import json
from flask import render_template

from ..utils import self_config_value


def to_debug(raw):
    """Dumps the raw data into the HTML page for debug purpose.

    :param raw: The data to dump
    """
    dump = json.dumps(raw, indent=2)
    return render_template(self_config_value('apidump_template'), dump=dump)
