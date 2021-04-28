from dynamodb_session_flask import Session
from flask import Flask, session


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
