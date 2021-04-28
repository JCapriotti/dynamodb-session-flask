import pytest
from flask import session
from . import create_test_app

LOCAL_DYNAMODB = {
    'SESSION_DYNAMODB_ENDPOINT_URL': 'http://localhost:8000'
}
USE_HEADER = {
    'SESSION_DYNAMODB_USE_HEADER': True
}


def test_save_and_load():
    expected_value = 'foo'
    # app = create_test_app({**LOCAL_DYNAMODB, **USE_HEADER})
    app = create_test_app(LOCAL_DYNAMODB)

    @app.route('/save')
    def save():
        session['val'] = expected_value
        return '', 200

    @app.route('/load')
    def load():
        return {
            'actual_value': session['val']
        }

    with app.test_client() as tc:
        response = tc.get('/save')

        response = tc.get('/load')

        assert response.json['actual_value'] == expected_value
