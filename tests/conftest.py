import boto3
import botocore
import pytest
from flask import Flask
from dynamodb_session_flask import Session

from .utility import LOCAL_ENDPOINT, TABLE_NAME


@pytest.fixture
def app():
    from flask import session

    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
    })

    @app.route('/')
    def test():
        session['foo'] = 'bar'
        return '', 200

    @app.route('/save/<val>')
    def save(val):
        from flask import session
        session['val'] = val
        return '', 200

    @app.route('/load')
    def load():
        from flask import session
        return {
            'actual_value': session.get('val', None),
        }

    yield app


@pytest.fixture
def client(app):
    def create_initialized_client(config):
        """
        Allows the Flask test client to be initialized with test-case specific configuration before being returned.
        """
        app.config.update(config)
        Session(app)
        return app.test_client()
    return create_initialized_client


@pytest.fixture(scope='function')
def dynamodb_table(docker_services):
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
