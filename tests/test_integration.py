from typing import Callable

import pytest
from pytest import param
from . import *


@pytest.mark.parametrize(
    'settings, header_func', [
        param(USE_HEADER, session_id_as_header, id='Use header')
    ]
)
@pytest.mark.usefixtures('dynamodb_table')
def test_save_and_load(settings, header_func: Callable):
    expected_value = 'foo'
    app = create_test_app(settings)

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
        # Test save and load
        r = tc.get('/save')
        h = header_func(tc)
        response = tc.get('/load', headers=h)

        assert response.json['actual_value'] == expected_value
