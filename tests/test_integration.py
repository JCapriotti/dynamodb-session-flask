import hashlib
from time import sleep

import pytest
from .utility import CookieSidHelper, get_dynamo_record, get_all_dynamo_records, HeaderSidHelper, \
    remove_dynamo_record, SidHelper, str_param


# pylint: disable=no-self-use
@pytest.mark.parametrize(
    'helper', [
        pytest.param(CookieSidHelper(), id='Cookie'),
        pytest.param(HeaderSidHelper(), id='Header'),
    ]
)
class TestWorkflows:
    def test_save_and_load_using_header(self, client, helper: SidHelper):
        expected_val_a = str_param()
        expected_val_b = str_param()

        with client(helper.configuration()) as client_a, client(helper.configuration()) as client_b:
            # Test save and load for two different requests
            r_a = client_a.get(f'/save/{expected_val_a}')
            r_b = client_b.get(f'/save/{expected_val_b}')

            response_a = client_a.get('/load', headers=helper.request_headers(r_a))
            response_b = client_b.get('/load', headers=helper.request_headers(r_b))

            assert response_a.json['actual_value'] == expected_val_a
            assert response_b.json['actual_value'] == expected_val_b

    def test_no_use_doesnt_save_anything(self, client, helper: SidHelper):
        with client(helper.configuration()) as test_client:
            resp = test_client.get('/no-session-use')
            sid = helper.sid(resp)

            assert sid is None
            assert len(get_all_dynamo_records()) == 0

    def test_no_use_followed_by_use_saves_session(self, client, helper: SidHelper):
        with client(helper.configuration()) as test_client:
            resp = test_client.get('/no-session-use')
            sid = helper.sid(resp)

            assert sid is None
            assert len(get_all_dynamo_records()) == 0

            resp = test_client.get('/save/foo')
            sid = helper.sid(resp)

            assert get_dynamo_record(sid) is not None

    def test_save_load_updates_expiration_after_load(self, client, helper: SidHelper):
        expected_session_value = str_param()

        with client(helper.configuration()) as test_client:
            resp = test_client.get(f'/save/{expected_session_value}')
            sid = helper.sid(resp)
            sleep(1)
            initial_expiration = get_dynamo_record(sid)['expires']

            test_client.get('/load', headers=helper.request_headers(resp))

            actual = get_dynamo_record(sid)
            assert actual['expires'] > initial_expiration

    def test_removed_sid_cant_be_reused(self, client, helper: SidHelper, flask_logs):
        """
        If a previously used session ID is no longer valid for a subsequent request, it isn't used. No session ID is
        returned if no data was saved.
        """
        with client(helper.configuration()) as test_client:
            original_response = test_client.get('/save/foo')
            original_sid = helper.sid(original_response)
            remove_dynamo_record(original_sid)

            new_response = test_client.get('/load', headers=helper.request_headers(original_response))
            new_sid = helper.sid(new_response)
            original_record = get_dynamo_record(original_sid)

            assert 'SessionNotFoundError' in flask_logs.text
            assert new_sid is None
            assert original_record is None

    def test_sid_cant_be_created(self, client, helper: SidHelper, flask_logs):
        with client(helper.configuration()) as test_client:
            bad_sid = str_param()
            if isinstance(helper, CookieSidHelper):
                test_client.set_cookie(None, 'id', bad_sid)
                response = test_client.get('/save/foo')
            else:
                response = test_client.get('/save/foo', headers={'x-id': bad_sid})

            sid = helper.sid(response)

            bad_sid_record = get_dynamo_record(bad_sid)
            good_record = get_dynamo_record(sid)

            assert 'SessionNotFoundError' in flask_logs.text
            assert bad_sid_record is None
            assert good_record is not None
            assert sid != bad_sid

    def test_failed_sid_is_available_as_member(self, client, helper: SidHelper, flask_logs):
        with client(helper.configuration()) as test_client:
            original_response = test_client.get('/save/foo')
            original_sid = helper.sid(original_response)
            expected_bad_sid_hash = hashlib.sha512(original_sid.encode()).hexdigest()
            remove_dynamo_record(original_sid)

            new_response = test_client.get('/check-bad-sid', headers=helper.request_headers(original_response))

            assert expected_bad_sid_hash in flask_logs.text
            assert new_response.json['failed_sid'] == expected_bad_sid_hash
            assert new_response.json['new']
