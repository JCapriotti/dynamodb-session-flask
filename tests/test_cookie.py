import pytest
from werkzeug.http import parse_cookie
from . import create_test_app


@pytest.mark.usefixtures('mock_save', 'mock_load')
def test_cookie_is_set_with_defaults():
    expected_cookie_name = 'id'
    expected_secure = True
    expected_http_only = True
    expected_same_site = 'Strict'

    app = create_test_app()
    with app.test_client() as tc:
        expected_cookie_value = app.session_interface._session.session_id

        response = tc.get('/')

        cookie = next(
            (cookie for cookie in response.headers.getlist('Set-Cookie') if expected_cookie_name in cookie),
            None
        )

        assert cookie is not None
        cookie_attrs = parse_cookie(cookie)

        assert cookie_attrs[expected_cookie_name] == expected_cookie_value
        assert ('Secure' in cookie_attrs) == expected_secure
        assert ('HttpOnly' in cookie_attrs) == expected_http_only
        assert cookie_attrs['SameSite'] == expected_same_site
        assert 'Domain' not in cookie_attrs
        assert 'Path' not in cookie_attrs


@pytest.mark.usefixtures('mock_save', 'mock_load')
def test_cookie_is_set_with_configured_settings():
    expected_cookie_name = 'foo'
    expected_secure = False
    expected_http_only = False
    expected_same_site = 'Lax'
    expected_domain = 'bar.com'
    expected_path = '/auth'

    config = {
        'SESSION_DYNAMODB_COOKIE_NAME': expected_cookie_name,
        'SESSION_DYNAMODB_COOKIE_SECURE': expected_secure,
        'SESSION_DYNAMODB_COOKIE_HTTP_ONLY': expected_http_only,
        'SESSION_DYNAMODB_COOKIE_SAME_SITE': expected_same_site,
        'SESSION_DYNAMODB_COOKIE_DOMAIN': expected_domain,
        'SESSION_DYNAMODB_COOKIE_PATH': expected_path,
    }

    app = create_test_app(config)
    with app.test_client() as tc:
        expected_cookie_value = app.session_interface._session.session_id

        response = tc.get('/')

        cookie = next(
            (cookie for cookie in response.headers.getlist('Set-Cookie') if expected_cookie_name in cookie),
            None
        )

        assert cookie is not None
        cookie_attrs = parse_cookie(cookie)

        assert cookie_attrs[expected_cookie_name] == expected_cookie_value
        assert ('Secure' in cookie_attrs) == expected_secure
        assert ('HttpOnly' in cookie_attrs) == expected_http_only
        assert cookie_attrs['SameSite'] == expected_same_site
        assert cookie_attrs['Domain'] == expected_domain
        assert cookie_attrs['Path'] == expected_path


def test_header_is_not_set():
    app = create_test_app()
    with app.test_client() as tc:
        response = tc.get('/')

        assert 'X-Id' not in response.headers
