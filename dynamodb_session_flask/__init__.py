from dynamodb_session_web import SessionCore, SessionDictInstance
from flask.sessions import SessionInterface, SessionMixin
from flask import Flask, session as flask_session

# noinspection PyTypeChecker
session: SessionDictInstance = flask_session


class Session(object):
    def __init__(self, app: Flask = None):
        self.app = app

        if self.app is not None:
            conf = app.config.copy()

            core_kwargs = {
                'sid_byte_length': conf.get('SESSION_DYNAMODB_SID_BYTE_LENGTH', None),
                'table_name': conf.get('SESSION_DYNAMODB_TABLE_NAME', None),
                'endpoint_url': conf.get('SESSION_DYNAMODB_ENDPOINT_URL', None),
            }
            flask_kwargs = {
                'use_header': conf.get('SESSION_DYNAMODB_USE_HEADER', False),
                'header_name': conf.get('SESSION_DYNAMODB_HEADER_NAME', 'X-Id'),

                'cookie_name': conf.get('SESSION_DYNAMODB_COOKIE_NAME', 'id'),
                'cookie_secure': conf.get('SESSION_DYNAMODB_COOKIE_SECURE', True),
                'cookie_http_only': conf.get('SESSION_DYNAMODB_COOKIE_HTTP_ONLY', True),
                'cookie_same_site': conf.get('SESSION_DYNAMODB_COOKIE_SAME_SITE', 'Strict'),
                'cookie_domain': conf.get('SESSION_DYNAMODB_COOKIE_DOMAIN', None),
                'cookie_path': conf.get('SESSION_DYNAMODB_COOKIE_PATH', None),

                'expose_actual_sid': conf.get('SESSION_DYNAMODB_EXPOSE_ACTUAL_SID', False)
            }
            actual_kwargs = {k: v for k, v in core_kwargs.items() if v is not None}
            actual_kwargs.update(flask_kwargs)

            app.session_interface = DynamoDbSession(**actual_kwargs)


class DynamoDbSessionInstance(SessionDictInstance, SessionMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cleared = False

    def clear(self):
        super().__init__()
        self.cleared = True


class DynamoDbSession(SessionInterface):
    def __init__(self, **kw):
        self._expose_actual_sid = kw.pop('expose_actual_sid')
        self._cookie_name = kw.pop('cookie_name')
        self._cookie_secure = kw.pop('cookie_secure')
        self._cookie_http_only = kw.pop('cookie_http_only')
        self._cookie_same_site = kw.pop('cookie_same_site')
        self._cookie_domain = kw.pop('cookie_domain')
        self._cookie_path = kw.pop('cookie_path')
        self._use_header = kw.pop('use_header')
        self._header_name = kw.pop('header_name')
        self._core_config = kw

    def open_session(self, app, request):
        session = SessionCore(DynamoDbSessionInstance, **self._core_config)
        if self._use_header:
            sid = request.headers.get(self._header_name)
        else:
            sid = request.cookies.get(self._cookie_name)

        if sid is None:
            instance = session.create()
        else:
            instance = session.load(sid)

        return instance

    def save_session(self, app, session_instance: DynamoDbSessionInstance, response):
        session = SessionCore(DynamoDbSessionInstance, **self._core_config)
        if session_instance.cleared:
            session.clear(session_instance.session_id)
            response.delete_cookie(self._cookie_name, domain=self._cookie_domain, path=self._cookie_path)
            return

        session.save(session_instance)

        if self._use_header:
            response.headers[self._header_name] = session_instance.session_id
        else:
            response.set_cookie(self._cookie_name,
                                session_instance.session_id,
                                secure=self._cookie_secure,
                                httponly=self._cookie_http_only,
                                samesite=self._cookie_same_site,
                                domain=self._cookie_domain,
                                path=self._cookie_path)
