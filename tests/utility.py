from random import randrange

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


def str_param() -> str:
    return str(randrange(100000))


def session_cookie_value(response: Response) -> str:
    cookie_key = 'id'
    cookie = next(
        (cookie for cookie in response.headers.getlist('Set-Cookie') if cookie_key in cookie),
        None
    )

    assert cookie is not None
    cookie_attrs = parse_cookie(cookie)

    return cookie_attrs[cookie_key]
