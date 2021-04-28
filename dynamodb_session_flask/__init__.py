from dynamodb_session_web import SessionCore
from flask.sessions import SessionInterface, SessionMixin
from flask import Flask


class Session(object):
    def __init__(self, app: Flask = None):
        self.app = app

        if self.app is not None:
            conf = app.config.copy()

            core_kwargs = {
                'sid_byte_length': conf.get('SESSION_DYNAMODB_SID_BYTE_LENGTH', None),
                'table_name': conf.get('SESSION_DYNAMODB_TABLE_NAME', None),
                'idle_timeout': conf.get('SESSION_DYNAMODB_IDLE_TIMEOUT', None),
                'absolute_timeout': conf.get('SESSION_DYNAMODB_ABSOLUTE_TIMEOUT', None),
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


class DynamoDbSessionData(dict, SessionMixin):
    def __init__(self, data, session_id):
        super().__init__()
        self.update(data)
        self.cleared = False
        self.session_id = session_id

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
        self._session = SessionCore(**kw)

    def open_session(self, app, request):
        if self._use_header:
            sid = request.headers.get(self._header_name)
        else:
            sid = request.cookies.get(self._cookie_name)

        if sid is None:
            data = {}
        else:
            data = self._session.load()

        returned_sid = self._session.session_id if self._expose_actual_sid else self._session.loggable_sid
        return DynamoDbSessionData(data, returned_sid)

    def save_session(self, app, session: DynamoDbSessionData, response):
        if session.cleared:
            self._session.clear()
            response.delete_cookie(self._cookie_name, domain=self._cookie_domain, path=self._cookie_path)
            return

        self._session.save(dict(session))

        if self._use_header:
            response.headers[self._header_name] = self._session.session_id
        else:
            response.set_cookie(self._cookie_name,
                                self._session.session_id,
                                secure=self._cookie_secure,
                                httponly=self._cookie_http_only,
                                samesite=self._cookie_same_site,
                                domain=self._cookie_domain,
                                path=self._cookie_path,
                                )
        self._session.save(session)
