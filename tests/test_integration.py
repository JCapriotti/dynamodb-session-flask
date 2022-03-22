from time import sleep

from .utility import cookie_config, get_dynamo_record, header_config, remove_dynamo_record, str_param


def test_save_and_load_using_header(client):
    expected_val_a = str_param()
    expected_val_b = str_param()

    with client(header_config()) as client_a, client(header_config()) as client_b:
        # Test save and load for two different requests
        r_a = client_a.get(f'/save/{expected_val_a}')
        r_b = client_b.get(f'/save/{expected_val_b}')

        sid_a = r_a.headers['x-id']
        sid_b = r_b.headers['x-id']

        response_a = client_a.get('/load', headers={'x-id': sid_a})
        response_b = client_b.get('/load', headers={'x-id': sid_b})

        assert response_a.json['actual_value'] == expected_val_a
        assert response_b.json['actual_value'] == expected_val_b


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


def test_no_use_doesnt_save_anything(client):
    with client(header_config()) as test_client:
        resp = test_client.get('/no-session-use')
        sid = resp.headers['x-id']

        assert get_dynamo_record(sid) is None


def test_no_use_followed_by_use_saves_session(client):
    with client(header_config()) as test_client:
        resp = test_client.get('/no-session-use')
        sid = resp.headers['x-id']

        assert get_dynamo_record(sid) is None

        test_client.get('/save/foo', headers={'x-id': sid})
        assert get_dynamo_record(sid) is not None


def test_save_load_updates_expiration_after_load(client):
    expected_session_value = str_param()

    with client(header_config()) as test_client:
        resp = test_client.get(f'/save/{expected_session_value}')
        sid = resp.headers['x-id']
        sleep(1)
        initial_expiration = get_dynamo_record(sid)['expires']

        test_client.get('/load', headers={'x-id': sid})

        actual = get_dynamo_record(sid)
        assert actual['expires'] > initial_expiration


def test_removed_sid_cant_be_reused_and_new_sid_created(client):
    with client(header_config()) as test_client:
        resp = test_client.get('/save/foo')
        original_sid = resp.headers['x-id']
        remove_dynamo_record(original_sid)

        test_client.get('/load', headers={'x-id': original_sid})

        actual = get_dynamo_record(original_sid)
        assert actual is None


def test_sid_cant_be_created(client):
    with client(header_config()) as test_client:
        bad_sid = str_param()
        test_client.get('/save/foo', headers={'x-id': bad_sid})

        actual = get_dynamo_record(bad_sid)
        assert actual is None
