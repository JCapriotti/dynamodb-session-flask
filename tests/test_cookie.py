from typing import cast

import pytest
from dynamodb_session_flask import DynamoDbSessionInstance
from flask import session
from werkzeug.http import parse_cookie

from .utility import cookie_config, str_param


@pytest.mark.usefixtures('dynamodb_table')
def test_cookie_is_set_with_defaults(client):
    expected_cookie_name = 'id'
    expected_secure = True
    expected_http_only = True
    expected_same_site = 'Strict'

    with client(cookie_config()) as tc:
        response = tc.get('/')

        assert isinstance(session, DynamoDbSessionInstance)
        expected_cookie_value = session.session_id

        cookie = next(
            (cookie for cookie in response.headers.getlist('Set-Cookie') if expected_cookie_name in cookie),
            None
        )

    assert cookie is not None
    cookie_attrs = parse_cookie(cookie)

    assert cookie_attrs[expected_cookie_name] == expected_cookie_value
    assert ('Secure' in cookie_attrs) == expected_secure
    assert ('HttpOnly' in cookie_attrs) == expected_http_only
    assert cookie_attrs['SameSite'] == expected_same_site
    assert 'Domain' not in cookie_attrs
    assert 'Path' not in cookie_attrs


@pytest.mark.usefixtures('dynamodb_table')
def test_cookie_is_set_with_configured_settings(client):
    expected_cookie_name = 'foo'
    expected_secure = False
    expected_http_only = False
    expected_same_site = 'Lax'
    expected_domain = 'bar.com'
    expected_path = '/auth'

    config = cookie_config() | {
        'SESSION_DYNAMODB_COOKIE_NAME': expected_cookie_name,
        'SESSION_DYNAMODB_COOKIE_SECURE': expected_secure,
        'SESSION_DYNAMODB_COOKIE_HTTP_ONLY': expected_http_only,
        'SESSION_DYNAMODB_COOKIE_SAME_SITE': expected_same_site,
        'SESSION_DYNAMODB_COOKIE_DOMAIN': expected_domain,
        'SESSION_DYNAMODB_COOKIE_PATH': expected_path,
    }

    with client(config) as tc:
        response = tc.get('/')

        assert isinstance(session, DynamoDbSessionInstance)
        expected_cookie_value = session.session_id

        cookie = next(
            (cookie for cookie in response.headers.getlist('Set-Cookie') if expected_cookie_name in cookie),
            None
        )

        assert cookie is not None
        cookie_attrs = parse_cookie(cookie)

        assert cookie_attrs[expected_cookie_name] == expected_cookie_value
        assert ('Secure' in cookie_attrs) == expected_secure
        assert ('HttpOnly' in cookie_attrs) == expected_http_only
        assert cookie_attrs['SameSite'] == expected_same_site
        assert cookie_attrs['Domain'] == expected_domain
        assert cookie_attrs['Path'] == expected_path


@pytest.mark.usefixtures('dynamodb_table')
def test_header_is_not_set(client):
    with client(cookie_config()) as tc:
        response = tc.get('/')

        assert 'X-Id' not in response.headers


@pytest.mark.usefixtures('dynamodb_table')
def test_header_id_is_not_used(client):
    """
    Make sure the header is not used for session ID, if we expect it to be in a cookie
    """
    saved_value = str_param()
    with client(cookie_config()) as tc:
        tc.get(f'/save/{saved_value}')
        session_id = cast(DynamoDbSessionInstance, session).session_id

    with client(cookie_config()) as tc:
        response = tc.get(f'/load', headers={'X-Id': session_id})

    assert response.json['actual_value'] != saved_value
