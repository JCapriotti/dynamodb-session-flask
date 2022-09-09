from abc import ABC, abstractmethod
from datetime import datetime
from random import randrange
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

import boto3
from flask import Response
from werkzeug.http import parse_cookie

TABLE_NAME = 'app_session'
LOCAL_ENDPOINT = 'http://localhost:8000'


def default_config() -> Dict[str, Any]:
    return {
        'SESSION_DYNAMODB_ENDPOINT_URL': LOCAL_ENDPOINT,
    }


def cookie_config() -> Dict[str, Any]:
    return {
        'SESSION_DYNAMODB_ENDPOINT_URL': LOCAL_ENDPOINT,
        'SESSION_DYNAMODB_USE_HEADER': False,
    }


def header_config() -> Dict[str, Any]:
    return {
        'SESSION_DYNAMODB_ENDPOINT_URL': LOCAL_ENDPOINT,
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

    if cookie is None:
        return {}
    return parse_cookie(cookie)


def get_dynamo_table():
    return boto3.resource('dynamodb', endpoint_url=LOCAL_ENDPOINT).Table(TABLE_NAME)


def get_dynamo_record(key) -> Optional[Dict[str, Any]]:
    table = get_dynamo_table()

    response = table.get_item(Key={'id': key}, ConsistentRead=True)
    return response.get('Item', None)


def get_all_dynamo_records() -> Optional[List[Dict[str, Any]]]:
    table = get_dynamo_table()

    response = table.scan()
    return response.get('Items', None)


def remove_dynamo_record(key) -> None:
    table = get_dynamo_table()

    table.delete_item(Key={'id': key})


def mock_current_datetime(mocker, val: datetime):
    """ This mocks the inner dynamodb_session_web, so we can control the created value. """
    mocker.patch('dynamodb_session_web._session.current_datetime', Mock(return_value=val))


def mock_current_timestamp(mocker, val: int):
    mocker.patch('dynamodb_session_flask._session.current_timestamp', Mock(return_value=val))


class SidHelper(ABC):
    """This is a base class to assist getting and using session IDs. The subclasses are used in parameterized tests
    to test either sessions that use the header or cookies.
    """
    @abstractmethod
    def configuration(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def sid(self, response: Response) -> str:
        pass

    @abstractmethod
    def request_headers(self, response: Response) -> Dict[str, str]:
        pass


class HeaderSidHelper(SidHelper):
    def configuration(self) -> Dict[str, Any]:
        return header_config()

    def sid(self, response: Response) -> str:
        return response.headers.get('x-id', None)

    def request_headers(self, response: Response) -> Dict[str, str]:
        return {'x-id': self.sid(response)}


class CookieSidHelper(SidHelper):
    def configuration(self) -> Dict[str, Any]:
        return cookie_config()

    def sid(self, response: Response) -> str:
        return session_cookie_dict(response).get('id', None)

    def request_headers(self, _) -> Dict[str, str]:
        return {}
