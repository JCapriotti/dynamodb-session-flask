import pytest
from dynamodb_session_flask import session
from dynamodb_session_web import SessionCore
from . import create_test_app


@pytest.mark.usefixtures('mock_save', 'mock_load')
def test_modified_session_settings():
    # TODO
    pass


@pytest.mark.usefixtures('mock_save', 'mock_load')
def test_defaults():
    app = create_test_app()

    # TODO more
    assert app.session_interface._cookie_name == 'id'
