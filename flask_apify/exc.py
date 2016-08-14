#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask_apify.exc
    ~~~~~~~~~~~~~~~

    The errors and exceptions that application API may produce.

    :copyright: (c) by Vital Kudzelka
"""
from werkzeug.exceptions import HTTPException


class ApiError(HTTPException):
    """Base class for all API errors."""
    code = None
    description = None


class ApiNotFound(ApiError):
    """Raise if the requested resource was not found on the server."""
    code = 404
    description = (
        "The requested resource was not found on the server. If you "
        "entered the URL manually please check your spelling and try again. "
    )


class ApiUnauthorized(ApiError):
    """Raise if the user is not authenticated but endpoint require
    authentication.
    """
    code = 401
    description = (
        "The server could not verify that you are authorized to access the "
        "requested URL."
    )


class ApiForbidden(ApiError):
    """Raise if the user is authenticated but does not have the permission for
    the requested resource.
    """
    code = 403
    description = (
        "You don\'t have the permission to access the requested resource."
    )


class ApiNotAcceptable(ApiError):
    """Raise if the application cannot return response in format that client
    accept.
    """
    code = 406
    description = (
        "The application API cannot generate response in format "
        "accepted by client according to the accept headers send "
        "in the request."
    )


class ApiUnprocessableEntity(ApiError):
    """Raise if the client send invalid fields in request."""
    code = 422
    description = (
        "The client missed required field or send invalid fields in request."
    )


class ApiNotImplemented(ApiError):
    """Raise if the application does not support the action requested by the
    client.
    """
    code = 501
    description = (
        "The API does not support the action requested by the client. "
        "To list of the supported API methods consult with the "
        "documentation. "
    )
