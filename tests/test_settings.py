import pytest
from dynamodb_session_web import SessionCore
from . import create_test_app


@pytest.mark.usefixtures('mock_save', 'mock_load')
def test_modified_session_settings():
    expected_sid_byte_length = 5
    expected_table_name = 'another_name'
    expected_idle_timeout = 3
    expected_absolute_timeout = 30
    expected_endpoint_url = 'foo'
    expected_expose_actual_sid = True

    config = {
        'SESSION_DYNAMODB_SID_BYTE_LENGTH': expected_sid_byte_length,
        'SESSION_DYNAMODB_TABLE_NAME': expected_table_name,
        'SESSION_DYNAMODB_IDLE_TIMEOUT': expected_idle_timeout,
        'SESSION_DYNAMODB_ABSOLUTE_TIMEOUT': expected_absolute_timeout,
        'SESSION_DYNAMODB_ENDPOINT_URL': expected_endpoint_url,
        'SESSION_DYNAMODB_EXPOSE_ACTUAL_SID': expected_expose_actual_sid,
    }

    app = create_test_app(config)
    with app.test_client() as tc:
        response = tc.get('/session_id')
        actual_sid = response.json['session_id']

    actual_session: SessionCore = app.session_interface._session
    expected_sid = actual_session.session_id

    assert actual_sid == expected_sid

    assert actual_session.sid_byte_length == expected_sid_byte_length
    assert actual_session.table_name == expected_table_name
    assert actual_session.idle_timeout == expected_idle_timeout
    assert actual_session.absolute_timeout == expected_absolute_timeout
    assert actual_session.endpoint_url == expected_endpoint_url


@pytest.mark.usefixtures('mock_save', 'mock_load')
def test_defaults():
    app = create_test_app()
    with app.test_client() as tc:
        response = tc.get('/session_id')
        actual_sid = response.json['session_id']

    actual_session: SessionCore = app.session_interface._session
    expected_sid = actual_session.loggable_sid

    assert actual_sid == expected_sid
