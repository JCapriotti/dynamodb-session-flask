from typing import cast

from flask import session

from dynamodb_session_flask import DynamoDbSessionInstance

dynamo_session = cast(DynamoDbSessionInstance, session)


def _testing_config() -> dict:
    return {'TESTING': True}


def test_able_to_use_test_session_transaction(client):
    expected_value = 'fake_value'

    with client(_testing_config()) as test_client:
        with test_client.session_transaction() as test_session:
            test_session['val'] = expected_value

        response = test_client.get('/load')

        assert response.json['actual_value'] == expected_value


def test_abandon(client):
    with client(_testing_config()) as test_client:
        response = test_client.get('/abandon')

        assert response.status_code == 200


def test_save(client):
    with client(_testing_config()) as test_client:
        response = test_client.get('/save')

        assert response.status_code == 200
