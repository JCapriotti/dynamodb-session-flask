import pytest
from flask import session

from dynamodb_session_flask import DynamoDbSessionInstance
from .utility import get_dynamo_record, header_config, int_param, str_param


@pytest.mark.usefixtures('dynamodb_table')
def test_header_with_default_settings(client):
    expected_header_name = 'x-id'

    with client(header_config()) as test_client:
        response = test_client.get('/')

        assert isinstance(session, DynamoDbSessionInstance)
        expected_header_value = session.session_id

        assert expected_header_name in response.headers
        assert response.headers[expected_header_name] == expected_header_value


@pytest.mark.usefixtures('dynamodb_table')
def test_header_with_configured_settings(client):
    expected_header_name = str_param()
    expected_idle_timeout = int_param()
    expected_absolute_timeout = int_param()

    config = {**header_config(), **{
        'SESSION_DYNAMODB_HEADER_NAME': expected_header_name,
        'SESSION_DYNAMODB_IDLE_TIMEOUT': expected_idle_timeout,
        'SESSION_DYNAMODB_ABSOLUTE_TIMEOUT': expected_absolute_timeout,
    }}
    with client(config) as test_client:
        response = test_client.get('/')

        assert isinstance(session, DynamoDbSessionInstance)
        expected_sid = session.session_id
        actual_record = get_dynamo_record(expected_sid)

        assert expected_header_name in response.headers
        assert response.headers[expected_header_name] == expected_sid
        assert actual_record['idle_timeout'] == expected_idle_timeout
        assert actual_record['absolute_timeout'] == expected_absolute_timeout


@pytest.mark.usefixtures('dynamodb_table')
def test_cookie_used_when_available(client):
    """
    We can allow a cookie to be used in place of header, when 'use header' setting is enabled
    """
    expected_value = str_param()

    with client(header_config()) as test_client:
        save_response = test_client.get(f'/save_items?val={expected_value}')

        sid = save_response.headers['x-id']

        test_client.set_cookie('', 'id', sid)
        load_response = test_client.get('/load')

        assert load_response.json['actual_value'] == expected_value
