# dynamodb-session-flask

An implementation of a Flask session using DynamoDB as backend storage. This project was built on 
[dynamodb-session-web](https://github.com/JCapriotti/dynamodb-session-web), but with support for the Flask framework.

## Why This Library?

I tried and acquired an appreciation for some other DynamoDB backend implementations for Flask sessions. 
However, I needed a few extra things:
* Absolute and Idle Timeouts
* Support for using a header (not a cookie) for session ID

In addition to the [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) 
best practices implemented in `dynamodb-session-web`, 
this project has additional support for these best practices:

* Non-descript session ID name - Defaults to `id` for cookies, and `x-id` for headers. 
  * Side-Comment - isn't a non-descript suggestion for a name actually descriptive?
* Cookie setting defaults:
  - [X] Secure = True
  - [X] HttpOnly = True
  - [X] SameSite = Strict
  - [ ] Domain and Path - Must set these yourself
* ID Exchange
  - [X] Accepted session ID mechanism (i.e. cookie vs header) is enforced. That is, user cannot submit session IDs 
        through a header if cookie is expected.

## Usage

Requires a DynamoDB table named `app_session` (can be changed in settings). 

Here's an example table creation statement:

```shell
aws dynamodb create-table \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
    --key-schema "AttributeName=id,KeyType=HASH" \
    --provisioned-throughput "ReadCapacityUnits=5,WriteCapacityUnits=5" \
    --table-name app_session 
```

Sessions are intended to operate just like the default Flask session implementation:

```python
from flask import Flask, session
from dynamodb_session_flask import DynamoDbSession

flask_app = Flask(__name__)
flask_app.session_interface = DynamoDbSession()

@flask_app.route('/save')
def save():
    session['val'] = 'My Value'
    return 'Success', 200

@flask_app.route('/load')
def load():
    saved_val = session['val']
    return saved_val, 200

@flask_app.route('/end')
def end_session():
    # This will remove the session from the database and remove the session ID from cookies/headers
    session.clear()
    return 'Success', 200
```

## Configuration

There are additional configuration options, and are set like normal Flask configuration:

```python
flask_app = Flask(__name__)
flask_app.config.update(
    SESSION_DYNAMODB_IDLE_TIMEOUT=600
)
```

All configuration is optional, assuming the defaults are okay.

### `SESSION_DYNAMODB_ABSOLUTE_TIMEOUT`
<div style="margin-left: 30px;">
Absolute session timeout (in seconds).

Note: This setting works in conjunction with Flask's [`PERMANENT_SESSION_LIFETIME`](https://flask.palletsprojects.com/en/2.0.x/config/#PERMANENT_SESSION_LIFETIME) setting.  The absolute timeout chosen will be whichever is less.

Default: `43200` (12 hours)
</div>

### `SESSION_DYNAMODB_ENDPOINT_URL`
<div style="margin-left: 30px;">
The DynamoDB URL.

Default: `None` (i.e. Boto3 logic)
</div>

### `SESSION_DYNAMODB_HEADER_NAME`
<div style="margin-left: 30px;">
The name of the header to use for the session ID.

Default: `x-id`
</div>

### `SESSION_DYNAMODB_IDLE_TIMEOUT`
<div style="margin-left: 30px;">
Idle session timeout (in seconds).

Default: `7200` (2 hours)
</div>

### `SESSION_DYNAMODB_SID_BYTE_LENGTH`
<div style="margin-left: 30px;">
Session ID length in bytes. 

This does not correlate to the character length of the ID, which will be either:

* 43 - How many characters a 32-byte value uses when Base64 encoded. 
* 71 - The 43 characters from the previous bullet, plus a dot and finally a 27-character HMAC signature. 

Default: `32`
</div>

### `SESSION_DYNAMODB_SID_KEYS`
<div style="margin-left: 30px;">
For a slightly more secure session ID, the key can be signed using a configurable and rotatable key. 

The signature is generated using [`itsdangerous`](https://itsdangerous.palletsprojects.com/en/2.1.x/) and includes key rotation. If/When rotation is desired, the array is used in order from oldest to newest. Otherwise, one key is all that is needed.

An empty array means no signature is generated.

Default: `[]` (no signature)
</div>

### `SESSION_DYNAMODB_TABLE_NAME`
<div style="margin-left: 30px;">
The name of the DynamoDB table.

Default: `app_session`
</div>

### `SESSION_DYNAMODB_OVERRIDE_COOKIE_NAME`
<div style="margin-left: 30px;">
Whether or not to override Flask's [SESSION_COOKIE_NAME](https://flask.palletsprojects.com/en/2.0.x/config/#SESSION_COOKIE_NAME)
configuration for the session ID. While somewhat trivial, OWASP's recommended value is 
`id` and Flask's default is `session`. So to avoid using Flask's default or modifying it behind the scenes, this setting
helps separate this library's preferred default from Flask's.

Setting this to `True` will set the cookie name to `id`. Otherwise, Flask's configuration will be used.

Default: `True`
</div>

### `SESSION_DYNAMODB_OVERRIDE_COOKIE_SECURE`
<div style="margin-left: 30px;">
Whether or not to override Flask's [`SESSION_COOKIE_SECURE`](https://flask.palletsprojects.com/en/2.0.x/config/#SESSION_COOKIE_SECURE)
for the cookie's Secure attribute. Flask defaults that attribute to `False`, whereas this should ideally be `True` to prevent 
Man-in-the-Middle attacks. 

Setting this to `True` will force the Secure attribute to also be `True`. Otherwise, Flask's configuration will be used.

Note: You'll want to set this to `False` in any environment where TLS is not used (e.g. local development).

Default: `True`
</div>

### `SESSION_DYNAMODB_USE_HEADER`
<div style="margin-left: 30px;">
Whether or not to communicate/expect the session ID via headers.

Default: `False`
</div>

### `SESSION_COOKIE_SAMESITE`
<div style="margin-left: 30px;">
This is actually a Flask configuration, which defaults to `None`. However, if the value is `None`, then we set it to 
`Strict` by default.

Default: `Strict` (indirectly changed)
</div>


## Testing

Flask has a [pattern for accessing the session](https://flask.palletsprojects.com/en/2.0.x/testing/#accessing-and-modifying-the-session) when running tests.
This mechanism still uses the backend `session_interface` set for the app (i.e. it will still use DynamoDB). 

To help reduce dependencies when simply trying to run unit tests that need a value set in the session, there's a 
separate `session_interface` that can be used.

Below is a working example, copied from [this project's tests](tests/test_testing.py). Improvements could be made depending on test expectations.

```python
import pytest
from dynamodb_session_flask.testing import TestSession
from flask import Flask, session


@pytest.fixture
def app():
    flask_app = Flask(__name__)

    @flask_app.route('/load')
    def load():
        return {
            'actual_value': session.get('val', None),
        }

    yield flask_app


@pytest.fixture()
def test_client(app):
    app.session_interface = TestSession()
    return app.test_client()


def test_able_to_use_test_session_transaction(test_client):
    expected_value = 'fake_value'

    with test_client:
        with test_client.session_transaction() as test_session:
            test_session['val'] = expected_value

        response = test_client.get('/load')

        assert response.json['actual_value'] == expected_value
```
