import pytest
from .utility import cookie_config, header_config, str_param


@pytest.mark.usefixtures('dynamodb_table')
def test_save_and_load_using_header(client):
    expected_val_a = str_param()
    expected_val_b = str_param()

    with client(header_config()) as client_a, client(header_config()) as client_b:
        # Test save and load for two different requests
        r_a = client_a.get(f'/save/{expected_val_a}')
        r_b = client_b.get(f'/save/{expected_val_b}')

        sid_a = r_a.headers['X-Id']
        sid_b = r_b.headers['X-Id']

        response_a = client_a.get('/load', headers={'X-Id': sid_a})
        response_b = client_b.get('/load', headers={'X-Id': sid_b})

        assert response_a.json['actual_value'] == expected_val_a
        assert response_b.json['actual_value'] == expected_val_b


@pytest.mark.usefixtures('dynamodb_table')
def test_save_and_load_using_cookie(client):
    expected_val_a = str_param()
    expected_val_b = str_param()

    with client(cookie_config()) as client_a, client(cookie_config()) as client_b:
        # Test save and load for two different requests
        client_a.get(f'/save/{expected_val_a}')
        client_b.get(f'/save/{expected_val_b}')

        response_a = client_a.get('/load')
        response_b = client_b.get('/load')

        assert response_a.json['actual_value'] == expected_val_a
        assert response_b.json['actual_value'] == expected_val_b
