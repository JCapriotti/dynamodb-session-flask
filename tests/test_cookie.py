from datetime import datetime, timedelta, timezone
from typing import cast

import pytest
from dateutil.parser import parse
from flask import session

from dynamodb_session_flask import DynamoDbSessionInstance
from .utility import cookie_config, get_dynamo_record, mock_current_datetime, mock_current_timestamp, \
    session_cookie_dict, str_param


@pytest.mark.usefixtures('dynamodb_table')
def test_cookie_is_set_with_defaults(client):
    expected_cookie_name = 'id'
    expected_secure = True
    expected_http_only = True
    expected_same_site = 'Strict'

    with client(cookie_config()) as test_client:
        response = test_client.get('/')

        assert isinstance(session, DynamoDbSessionInstance)
        expected_cookie_value = session.session_id

        cookie_dict = session_cookie_dict(response, expected_cookie_name)

    assert cookie_dict[expected_cookie_name] == expected_cookie_value
    assert ('Secure' in cookie_dict) == expected_secure
    assert ('HttpOnly' in cookie_dict) == expected_http_only
    assert cookie_dict['SameSite'] == expected_same_site
    assert 'Domain' not in cookie_dict
    assert cookie_dict['Path'] == '/'


@pytest.mark.usefixtures('dynamodb_table')
def test_clear(client):
    with client(cookie_config()) as test_client:
        resp = test_client.get('/save_items?val=foo')
        initial_cookie = session_cookie_dict(resp, 'id')
        sid = initial_cookie['id']

        resp = test_client.get('/clear')
        final_cookie = session_cookie_dict(resp, 'id')

        actual = get_dynamo_record(sid)
        assert actual is None
        assert final_cookie['id'] == ''
        assert parse(final_cookie['Expires']) == datetime.fromtimestamp(0, tz=timezone.utc)


@pytest.mark.usefixtures('dynamodb_table')
def test_cookie_is_set_with_flask_configured_settings(client):
    expected_cookie_name = 'foo'
    expected_secure = False
    expected_http_only = False
    expected_same_site = 'Lax'
    expected_domain = 'bar.com'
    expected_path = '/auth'

    config = cookie_config() | {
        'SESSION_DYNAMODB_OVERRIDE_COOKIE_NAME': False,
        'SESSION_DYNAMODB_OVERRIDE_COOKIE_SECURE': False,
        'SESSION_COOKIE_NAME': expected_cookie_name,
        'SESSION_COOKIE_SECURE': expected_secure,
        'SESSION_COOKIE_HTTPONLY': expected_http_only,
        'SESSION_COOKIE_SAMESITE': expected_same_site,
        'SESSION_COOKIE_DOMAIN': expected_domain,
        'SESSION_COOKIE_PATH': expected_path,
    }

    with client(config) as test_client:
        response = test_client.get('/')

        assert isinstance(session, DynamoDbSessionInstance)
        expected_cookie_value = session.session_id
        cookie_dict = session_cookie_dict(response, expected_cookie_name)

        assert cookie_dict[expected_cookie_name] == expected_cookie_value
        assert ('Secure' in cookie_dict) == expected_secure
        assert ('HttpOnly' in cookie_dict) == expected_http_only
        assert cookie_dict['SameSite'] == expected_same_site
        assert cookie_dict['Domain'] == expected_domain
        assert cookie_dict['Path'] == expected_path


@pytest.mark.usefixtures('dynamodb_table')
def test_header_is_not_set(client):
    with client(cookie_config()) as test_client:
        response = test_client.get('/')

        assert 'x-id' not in response.headers


@pytest.mark.usefixtures('dynamodb_table')
def test_header_id_is_not_used(client):
    """
    Make sure the header is not used for session ID, if we expect it to be in a cookie
    """
    saved_value = str_param()
    with client(cookie_config()) as test_client:
        test_client.get(f'/save_items?val={saved_value}')
        session_id = cast(DynamoDbSessionInstance, session).session_id

    with client(cookie_config()) as test_client:
        response = test_client.get('/load', headers={'x-id': session_id})

    assert response.json['actual_value'] != saved_value


@pytest.mark.parametrize(
    'absolute, flask_permanent_lifetime, expected', [
        pytest.param(120, 230, 120, id='Absolute is less than Permanent setting'),
        pytest.param(160, 140, 140, id='Permanent setting is less than Absolute'),
    ]
)
@pytest.mark.usefixtures('dynamodb_table')
def test_expiration_settings_used_for_cookie(mocker, client, absolute, flask_permanent_lifetime, expected):
    """ Check that the session cookie expiration is the minimum of either the absolute timeout or the Flaks config's
    PERMANENT_SESSION_LIFETIME setting.

    These tests ignore idle timeout to keep them simple.
    """
    config = cookie_config() | {
        'SESSION_DYNAMODB_ABSOLUTE_TIMEOUT': absolute,
        'PERMANENT_SESSION_LIFETIME': flask_permanent_lifetime,
    }

    current_datetime = datetime(1977, 12, 28, 12, 40, 0, 0, tzinfo=timezone.utc)
    mock_current_datetime(mocker, current_datetime)

    with client(config) as test_client:
        resp = test_client.get('/save_items?val=foo')
        cookie_dict = session_cookie_dict(resp, 'id')

        assert parse(cookie_dict['Expires']) == current_datetime + timedelta(seconds=expected)


@pytest.mark.parametrize(
    'idle, absolute, expected', [
        pytest.param(20, 30, 20, id='Idle is less than Absolute setting'),
        pytest.param(80, 40, 40, id='Absolute setting is less than Idle'),
    ]
)
@pytest.mark.usefixtures('dynamodb_table')
def test_idle_timeout_expiration_for_cookie(mocker, client, idle, absolute, expected):
    """ Check that the session cookie expiration is the minimum of either the idle timeout or absolute timeout

    These tests ignore PERMANENT_SESSION_LIFETIME to keep them simple. Flask's default is 31 days.
    """
    config = cookie_config() | {
        'SESSION_DYNAMODB_IDLE_TIMEOUT': idle,
        'SESSION_DYNAMODB_ABSOLUTE_TIMEOUT': absolute,
    }

    current_datetime = datetime(1977, 12, 28, 12, 40, 0, 0, tzinfo=timezone.utc)
    mock_current_datetime(mocker, current_datetime)
    mock_current_timestamp(mocker, int(current_datetime.timestamp()))

    with client(config) as test_client:
        resp = test_client.get('/save_items?val=foo')
        cookie_dict = session_cookie_dict(resp, 'id')

        assert parse(cookie_dict['Expires']) == current_datetime + timedelta(seconds=expected)
