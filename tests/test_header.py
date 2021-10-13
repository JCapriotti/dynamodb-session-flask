import pytest
from dynamodb_session_flask import session
from . import create_test_app


@pytest.mark.usefixtures('mock_save', 'mock_load')
def test_header_with_default_settings():
    expected_header_name = 'X-Id'
    config = {
        'SESSION_DYNAMODB_USE_HEADER': True,
    }

    app = create_test_app(config)
    with app.test_client() as tc:
        response = tc.get('/')
        expected_header_value = session.session_id

        assert expected_header_name in response.headers
        assert response.headers[expected_header_name] == expected_header_value


@pytest.mark.usefixtures('mock_save', 'mock_load')
def test_header_with_configured_settings():
    expected_header_name = 'foo'

    config = {
        'SESSION_DYNAMODB_USE_HEADER': True,
        'SESSION_DYNAMODB_HEADER_NAME': expected_header_name,
    }

    app = create_test_app(config)
    with app.test_client() as tc:
        response = tc.get('/')
        expected_header_value = session.session_id

        assert expected_header_name in response.headers
        assert response.headers[expected_header_name] == expected_header_value
