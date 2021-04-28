import pytest
from dynamodb_session_flask import SessionCore
from pytest_mock import MockerFixture


@pytest.fixture
def mock_save(mocker: MockerFixture):
    return mocker.patch.object(SessionCore, 'save')


@pytest.fixture
def mock_load(mocker: MockerFixture):
    return mocker.patch.object(SessionCore, 'load')
