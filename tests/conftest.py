import boto3
import botocore
import pytest
from flask import Flask, session

from dynamodb_session_flask import DynamoDbSession, FlaskNullSessionInstance
from dynamodb_session_web.exceptions import SessionError

from .utility import LOCAL_ENDPOINT, TABLE_NAME


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    flask_app.config.update({
        'TESTING': True,
    })

    @flask_app.route('/')
    def test():
        session['foo'] = 'bar'
        return '', 200

    @flask_app.route('/save/<val>')
    def save(val):
        session['val'] = val
        return '', 200

    @flask_app.route('/load')
    def load():
        return {
            'actual_value': session.get('val', None),
        }

    @flask_app.route('/no-session-use')
    def no_session_use():
        return '', 200

    @flask_app.route('/clear')
    def clear():
        session.clear()
        return '', 200

    yield flask_app


@pytest.fixture
def client(app):  # pylint: disable=redefined-outer-name
    def create_initialized_client(config):
        """
        Allows the Flask test client to be initialized with test-case specific configuration before being returned.
        """
        app.config.update(config)
        app.session_interface = DynamoDbSession()
        return app.test_client()
    return create_initialized_client


@pytest.fixture(scope='function', autouse=True)
def dynamodb_table(docker_services):  # pylint: disable=unused-argument
    dynamodb = boto3.resource('dynamodb', endpoint_url=LOCAL_ENDPOINT)

    # Remove table (if it exists)
    # noinspection PyUnresolvedReferences
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.delete()
    except botocore.exceptions.ClientError as exc:
        if exc.response.get('Error', {}).get('Code') == 'ResourceNotFoundException':
            pass

    # Create the DynamoDB table.
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{
            'AttributeName': 'id',
            'KeyType': 'HASH'
        }],
        AttributeDefinitions=[{
            'AttributeName': 'id',
            'AttributeType': 'S'
        }],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_NAME)
    yield
    table.delete()
