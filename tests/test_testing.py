from typing import cast

import pytest
from flask import Flask, session

from dynamodb_session_flask import DynamoDbSessionInstance
from dynamodb_session_flask.testing import TestSession

dynamo_session = cast(DynamoDbSessionInstance, session)


@pytest.fixture
def app():
    flask_app = Flask(__name__)

    @flask_app.route('/load')
    def load():
        return {
            'actual_value': session.get('val', None),
        }

    @flask_app.route('/abandon')
    def abandon():
        dynamo_session.abandon()
        return '', 200

    yield flask_app


@pytest.fixture()
def test_client(app):  # pylint: disable=redefined-outer-name
    app.session_interface = TestSession()
    return app.test_client()


def test_able_to_use_test_session_transaction(test_client):  # pylint: disable=redefined-outer-name
    expected_value = 'fake_value'

    with test_client:
        with test_client.session_transaction() as test_session:
            test_session['val'] = expected_value

        response = test_client.get('/load')

        assert response.json['actual_value'] == expected_value


def test_abandon(test_client):  # pylint: disable=redefined-outer-name
    with test_client:
        response = test_client.get('/abandon')

        assert response.status_code == 200
