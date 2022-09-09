import hashlib
import json
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
            r_a = client_a.get(f'/save?val={expected_val_a}')
            r_b = client_b.get(f'/save?val={expected_val_b}')

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
        """
        Make sure that no session use does not save anything or return a SID.
        Then when the session is used, verify that a SID is returned and session is saved.
        For header use, it should send back the ID in a dedicated header, and cookie.
        """
        with client(helper.configuration()) as test_client:
            resp = test_client.get('/no-session-use')
            sid = helper.sid(resp)

            assert sid is None
            assert len(get_all_dynamo_records()) == 0

            resp = test_client.get('/save?val=foo')
            sid = helper.sid(resp)

            assert get_dynamo_record(sid) is not None

            if isinstance(helper, HeaderSidHelper):
                cookie_sid = CookieSidHelper().sid(resp)
                assert cookie_sid == sid

    def test_save_load_updates_expiration_after_load(self, client, helper: SidHelper):
        expected_session_value = str_param()

        with client(helper.configuration()) as test_client:
            resp = test_client.get(f'/save?val={expected_session_value}')
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
            original_response = test_client.get('/save?val=foo')
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
                response = test_client.get('/save?val=foo')
            else:
                response = test_client.get('/save?val=foo', headers={'x-id': bad_sid})

            sid = helper.sid(response)

            bad_sid_record = get_dynamo_record(bad_sid)
            good_record = get_dynamo_record(sid)

            assert 'SessionNotFoundError' in flask_logs.text
            assert bad_sid_record is None
            assert good_record is not None
            assert sid != bad_sid

    def test_failed_sid_is_available_as_member(self, client, helper: SidHelper, flask_logs):
        with client(helper.configuration()) as test_client:
            original_response = test_client.get('/save?val=foo')
            original_sid = helper.sid(original_response)
            expected_bad_sid_hash = hashlib.sha512(original_sid.encode()).hexdigest()
            remove_dynamo_record(original_sid)

            new_response = test_client.get('/check-bad-sid', headers=helper.request_headers(original_response))

            assert expected_bad_sid_hash in flask_logs.text
            assert new_response.json['failed_sid'] == expected_bad_sid_hash
            assert new_response.json['new'] is True

    def test_abandon_removes_session_record_mid_request(self, client, helper: SidHelper):
        expected_val_a = str_param()
        expected_val_b = str_param()

        with client(helper.configuration()) as client_a, client(helper.configuration()) as client_b:
            # First save a couple of sessions
            resp_a = client_a.get(f'/save?val={expected_val_a}')
            resp_b = client_b.get(f'/save?val={expected_val_b}')

            sid_a = helper.sid(resp_a)
            sid_b = helper.sid(resp_b)

            assert get_dynamo_record(sid_a) is not None
            assert get_dynamo_record(sid_b) is not None

            # Clear the "A" session. This should raise an error if the session record is not removed.
            abandon_response = client_a.get('/abandon-and-assert', headers=helper.request_headers(resp_a))
            assert abandon_response.status_code == 200

            # Do more assertions
            assert get_dynamo_record(sid_a) is None
            assert get_dynamo_record(sid_b) is not None

            # Clearing the cookie using Flask's helper sets the value to empty string,
            # whereas the header will be None.
            assert not helper.sid(abandon_response)

    def test_new_creates_new_session_id(self, client, helper: SidHelper):
        """
        Calling new() creates a new session ID, but does not abandon the old record.
        New record is not saved until data is modified.
        """
        expected_val = str_param()

        with client(helper.configuration()) as test_client:
            first_resp = test_client.get(f'/save?val={expected_val}')
            original_sid = helper.sid(first_resp)

            new_resp = test_client.get('/new', headers=helper.request_headers(first_resp))
            new_sid = helper.sid(new_resp)

            assert get_dynamo_record(original_sid) is not None
            assert new_sid is None

    def test_new_with_save_creates_new_session_record(self, client, helper: SidHelper):
        """
        Calling new() creates a new session ID, but does not abandon the old record.
        New record is not saved until data is modified.
        No data should be persisted between the original and new sessions.
        """
        original_expected_val = str_param()
        original_expected_val_2 = str_param()
        new_expected_val = str_param()

        with client(helper.configuration()) as test_client:
            first_resp = test_client.get(f'/save?val={original_expected_val}&val_2={original_expected_val_2}')
            original_sid = helper.sid(first_resp)

            new_resp = test_client.get(
                f'/new-and-save?val={new_expected_val}',
                headers=helper.request_headers(first_resp))
            new_sid = helper.sid(new_resp)

            assert original_sid != new_sid

            original_record = get_dynamo_record(original_sid)
            new_record = get_dynamo_record(new_sid)

            expected_original = json.dumps({'val': original_expected_val, 'val_2': original_expected_val_2})
            expected_new = json.dumps({'val': new_expected_val})

            assert original_record['data'] == expected_original
            assert new_record['data'] == expected_new

    def test_manual_save_creates_record(self, client, helper: SidHelper):
        """
        Tests the save() method and makes sure it does not conflict with when Flask saves the session.

        Might be unnecessary, but it does this by:
         - Adding a value to the session (manually_saved_val), and calls save()
         - Adds another value to the session (flask_saved_val) and lets Flask's default behavior save it.

        Within the test web request, it asserts that the first save works.
        Within the test below, it asserts that both the first and second values are persisted.
        """
        manually_saved_val = str_param()
        flask_saved_val = str_param()
        with client(helper.configuration()) as test_client:
            resp = test_client.get(f'/manual-save-and-assert?manual={manually_saved_val}&flask={flask_saved_val}')
            assert resp.status_code == 200

            # Check the final state of the database
            sid = helper.sid(resp)
            record = get_dynamo_record(sid)
            session_data = json.loads(record['data'])

            assert get_dynamo_record(sid) is not None
            assert session_data['manual'] == manually_saved_val
            assert session_data['flask'] == flask_saved_val
