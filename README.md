# dynamodb-session-flask

An implementation of a Flask session using DynamoDB as backend storage. This project was built on 
[dynamodb-session-web](https://github.com/JCapriotti/dynamodb-session-web), but with support for the Flask framework.

In addition to the [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) 
best practices implemented in `dynamodb-session-web`, this project has additional support for these best practices:

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

<dl>

<dt><code>SESSION_DYNAMODB_ABSOLUTE_TIMEOUT</code></dt>
<dd>
Absolute session timeout (in seconds).

Note: This setting works in conjunction with Flask's [`PERMANENT_SESSION_LIFETIME`](https://flask.palletsprojects.com/en/2.0.x/config/#PERMANENT_SESSION_LIFETIME) setting.  The absolute timeout chosen will be whichever is less.

Default: `43200` (12 hours)
</dd>

<dt><code>SESSION_DYNAMODB_ENDPOINT_URL</code></dt>
<dd>
The DynamoDB URL.

Default: `None` (i.e. Boto3 logic)
</dd>

<dt><code>SESSION_DYNAMODB_HEADER_NAME</code></dt>
<dd>
The name of the header to use for the session ID.

Default: `x-id`
</dd>

<dt><code>SESSION_DYNAMODB_IDLE_TIMEOUT</code></dt>
<dd>
Idle session timeout (in seconds).

Default: `7200` (2 hours)
</dd>

<dt><code>SESSION_DYNAMODB_SID_BYTE_LENGTH</code></dt>
<dd>
Session ID length in bytes. 

This does not correlate to the character length of the ID, which will be either:

* 43 - How many characters a 32-byte value uses when Base64 encoded. 
* 71 - The 43 characters from the previous bullet, plus a dot and finally a 27-character HMAC signature. 

Default: `32`
</dd>

<dt><code>SESSION_DYNAMODB_SID_KEYS</code></dt>
<dd>
For a slightly more secure session ID, the key can be signed using a configurable and rotatable key. 

The signature is generated using [`itsdangerous`](https://itsdangerous.palletsprojects.com/en/2.1.x/) and includes key rotation. If/When rotation is desired, the array is used in order from oldest to newest. Otherwise, one key is all that is needed.

An empty array means no signature is generated.

Default: `[]` (no signature)
</dd>

<dt><code>SESSION_DYNAMODB_TABLE_NAME</code></dt>
<dd>
The name of the DynamoDB table.

Default: `app_session`
</dd>

<dt><code>SESSION_DYNAMODB_OVERRIDE_COOKIE_NAME</code></dt>
<dd>
Whether or not to override Flask's [SESSION_COOKIE_NAME](https://flask.palletsprojects.com/en/2.0.x/config/#SESSION_COOKIE_NAME)
configuration for the session ID. While somewhat trivial, OWASP's recommended value is 
`id` and Flask's default is `session`. So to avoid using Flask's default or modifying it behind the scenes, this setting
helps separate this library's preferred default from Flask's.

Setting this to `True` will set the cookie name to `id`. Otherwise, Flask's configuration will be used.

Default: `True`
</dd>

<dt><code>SESSION_DYNAMODB_OVERRIDE_COOKIE_SECURE</code></dt>
<dd>
Whether or not to override Flask's [`SESSION_COOKIE_SECURE`](https://flask.palletsprojects.com/en/2.0.x/config/#SESSION_COOKIE_SECURE)
for the cookie's Secure attribute. Flask defaults that attribute to `False`, whereas this should ideally be `True` to prevent 
Man-in-the-Middle attacks. 

Setting this to `True` will force the Secure attribute to also be `True`. Otherwise, Flask's configuration will be used.

Note: You'll want to set this to `False` in any environment where TLS is not used (e.g. local development).

Default: `True`
</dd>

<dt><code>SESSION_DYNAMODB_USE_HEADER</code></dt>
<dd>
Whether or not to communicate/expect the session ID via headers.

Default: `False`
</dd>

<dt><code>SESSION_COOKIE_SAMESITE</code></dt>
<dd>
This is actually a Flask configuration, which defaults to `None`. However, if the value is `None`, then we set it to 
`Strict` by default.

Default: `Strict` (indirectly changed)
</dd>

</dl>