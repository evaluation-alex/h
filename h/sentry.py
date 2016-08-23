# -*- coding: utf-8 -*-
"""
Provide a Sentry client at `request.sentry`.

This module provides a Sentry client, preconfigured with appropriate request
context, as a request property, `request.sentry`. This allows us to more easily
log exceptions from within the application with a useful complement of
diagnostic data.
"""

import raven
from raven.transport import GeventedHTTPTransport
from raven.utils.wsgi import get_environ

from h import __version__

PROCESSORS = (
    'raven.processors.SanitizePasswordsProcessor',
    'raven.processors.RemovePostDataProcessor',
)


def http_context_data(request):
    return {
        'url': request.url,
        'method': request.method,
        'data': request.body,
        'query_string': request.query_string,
        'cookies': dict(request.cookies),
        'headers': dict(request.headers),
        'env': dict(get_environ(request.environ)),
    }


def user_context_data(request):
    return {
        'id': request.authenticated_userid,
        'ip_address': request.client_addr,
    }


def get_client(settings):
    """
    Get a Sentry client configured with context data for the current request.
    """
    # If the `raven.transport` setting is set to 'gevent', then we use the
    # raven-supplied gevent compatible transport.
    transport_name = settings.get('raven.transport')
    transport = GeventedHTTPTransport if transport_name == 'gevent' else None

    return raven.Client(release=__version__,
                        transport=transport,
                        processors=PROCESSORS)


def _get_request_client(request):
    client = get_client(request.registry.settings)
    client.http_context(http_context_data(request))
    client.user_context(user_context_data(request))
    return client


def includeme(config):
    config.add_request_method(_get_request_client, 'sentry', reify=True)
