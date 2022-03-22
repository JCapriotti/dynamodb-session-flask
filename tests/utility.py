from datetime import datetime
from random import randrange
from typing import Any, Dict, Optional
from unittest.mock import Mock

import boto3
from flask import Response
from werkzeug.http import parse_cookie

TABLE_NAME = 'app_session'
LOCAL_ENDPOINT = 'http://localhost:8000'


def cookie_config():
    return {
        'SESSION_DYNAMODB_ENDPOINT_URL': LOCAL_ENDPOINT,
        'SESSION_DYNAMODB_EXPOSE_ACTUAL_SID': True,
        'SESSION_DYNAMODB_USE_HEADER': False,
    }


def header_config():
    return {
        'SESSION_DYNAMODB_ENDPOINT_URL': LOCAL_ENDPOINT,
        'SESSION_DYNAMODB_EXPOSE_ACTUAL_SID': True,
        'SESSION_DYNAMODB_USE_HEADER': True,
    }


def int_param() -> int:
    return randrange(100000)


def str_param() -> str:
    return str(randrange(100000))


def session_cookie_dict(response: Response, key: str = 'id') -> Dict[str, str]:
    cookie = next(
        (cookie for cookie in response.headers.getlist('Set-Cookie') if key in cookie),
        None
    )

    assert cookie is not None
    return parse_cookie(cookie)


def get_dynamo_resource():
    return boto3.resource('dynamodb', endpoint_url=LOCAL_ENDPOINT)


def get_dynamo_record(key) -> Optional[Dict[str, Any]]:
    dynamodb = get_dynamo_resource()
    table = dynamodb.Table(TABLE_NAME)

    response = table.get_item(Key={'id': key})
    return response.get('Item', None)


def remove_dynamo_record(key) -> None:
    dynamodb = get_dynamo_resource()
    table = dynamodb.Table(TABLE_NAME)

    table.delete_item(Key={'id': key})


def mock_current_datetime(mocker, val: datetime):
    """ This mocks the inner dynamodb_session_web, so we can control the created value. """
    mocker.patch('dynamodb_session_web._session.current_datetime', Mock(return_value=val))


def mock_current_timestamp(mocker, val: int):
    mocker.patch('dynamodb_session_flask._session.current_timestamp', Mock(return_value=val))
