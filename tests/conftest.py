import boto3
import botocore
import pytest
from dynamodb_session_flask import SessionCore
from pytest_mock import MockerFixture
from . import *


@pytest.fixture
def mock_save(mocker: MockerFixture):
    return mocker.patch.object(SessionCore, 'save')


@pytest.fixture
def mock_load(mocker: MockerFixture):
    return mocker.patch.object(SessionCore, 'load')


@pytest.fixture(scope='function')
def dynamodb_table(docker_services):
    dynamodb = boto3.resource('dynamodb', endpoint_url=LOCAL_ENDPOINT)

    # Remove table (if it exists)
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.delete()
    except botocore.exceptions.ClientError:
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
