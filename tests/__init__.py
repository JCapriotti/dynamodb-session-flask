from dynamodb_session_flask import Session, session
from flask import Flask

TABLE_NAME = 'app_session'
LOCAL_ENDPOINT = 'http://localhost:8000'

USE_HEADER = {
    'SESSION_DYNAMODB_ENDPOINT_URL': LOCAL_ENDPOINT,
    'SESSION_DYNAMODB_EXPOSE_ACTUAL_SID': True,
    'SESSION_DYNAMODB_USE_HEADER': True,
}
USE_COOKIE = {
    'SESSION_DYNAMODB_ENDPOINT_URL': LOCAL_ENDPOINT,
    'SESSION_DYNAMODB_EXPOSE_ACTUAL_SID': True,
    'SESSION_DYNAMODB_USE_HEADER': False,
}


def create_test_app(config: dict = None):
    config = {} if config is None else config

    app = Flask(__name__)
    app.config.update(config)
    Session(app)

    @app.route('/')
    def test():
        session['foo'] = 'bar'
        return '', 200

    @app.route('/session_id')
    def session_id():
        return {
            'session_id': session.session_id
        }

    return app


def session_id_as_header(test_client):
    """
    Helper to call the ``session_id`` endpoint, get the session ID, and return as a dict for use as a header.
    """
    response = test_client.get('/session_id')
    actual_sid = response.json['session_id']
    return {'X-Id': actual_sid}
