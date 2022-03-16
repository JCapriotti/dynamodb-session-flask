import pytest
from dynamodb_session_flask import DynamoDbSessionInstance
from flask import session

from .utility import header_config


@pytest.mark.usefixtures('dynamodb_table')
def test_header_with_default_settings(client):
    expected_header_name = 'X-Id'

    with client(header_config()) as tc:
        response = tc.get('/')

        assert isinstance(session, DynamoDbSessionInstance)
        expected_header_value = session.session_id

        assert expected_header_name in response.headers
        assert response.headers[expected_header_name] == expected_header_value


@pytest.mark.usefixtures('dynamodb_table')
def test_header_with_configured_settings(client):
    expected_header_name = 'foo'

    config = header_config() | {'SESSION_DYNAMODB_HEADER_NAME': expected_header_name}
    with client(config) as tc:
        response = tc.get('/')

        assert isinstance(session, DynamoDbSessionInstance)
        expected_header_value = session.session_id

        assert expected_header_name in response.headers
        assert response.headers[expected_header_name] == expected_header_value
