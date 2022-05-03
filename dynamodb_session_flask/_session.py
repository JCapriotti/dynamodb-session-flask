import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, cast, List

from dynamodb_session_web import SessionManager, SessionDictInstance
from dynamodb_session_web.exceptions import SessionError
from flask import current_app, Flask
from flask.sessions import SessionInterface, SessionMixin
from flask.wrappers import Request, Response

DEFAULT_COOKIE_NAME = 'id'
DEFAULT_COOKIE_SAMESITE = 'Strict'
DEFAULT_COOKIE_SECURE = True
DEFAULT_HEADER_NAME = 'x-id'
DEFAULT_SID_KEYS: List[str] = []


def current_datetime(datetime_value: datetime = None) -> datetime:
    if datetime_value is None:
        datetime_value = datetime.now(tz=timezone.utc)
    return datetime_value


def current_timestamp(datetime_value: datetime = None) -> int:
    return int(current_datetime(datetime_value).timestamp())


def session_manager_configuration(app: Flask) -> Dict[str, Any]:
    absolute_cfg = app.config.get('SESSION_DYNAMODB_ABSOLUTE_TIMEOUT', None)
    permanent_lifetime_cfg = int(cast(timedelta, app.permanent_session_lifetime).total_seconds())

    if absolute_cfg:
        absolute_timeout = min(absolute_cfg, permanent_lifetime_cfg)
    else:
        absolute_timeout = permanent_lifetime_cfg

    core_kwargs = {
        'sid_byte_length': app.config.get('SESSION_DYNAMODB_SID_BYTE_LENGTH', None),
        'table_name': app.config.get('SESSION_DYNAMODB_TABLE_NAME', None),
        'endpoint_url': app.config.get('SESSION_DYNAMODB_ENDPOINT_URL', None),
        'idle_timeout_seconds': app.config.get('SESSION_DYNAMODB_IDLE_TIMEOUT', None),
        'absolute_timeout_seconds': absolute_timeout,
        'sid_keys': app.config.get('SESSION_DYNAMODB_SID_KEYS', DEFAULT_SID_KEYS),
        'bad_session_id_raises': True,
    }

    return {k: v for k, v in core_kwargs.items() if v is not None}


def create_session_manager(app: Flask) -> SessionManager:
    mgr = SessionManager(DynamoDbSessionInstance, **session_manager_configuration(app))
    mgr.null_session_class = FlaskNullSessionInstance
    return mgr


class DynamoDbSessionInstance(SessionDictInstance, SessionMixin):
    """
    Allows tracking of an SID that was invalid.
    Returned value is actually the hex digest of the SHA-512 hash of the SID.
    """
    failed_sid: str = ''

    def __init__(self, **kwargs):
        self.cleared = False
        self.modified = False
        super().__init__(**kwargs)

    def clear(self):
        """
        Clears the session data.
        At the end of the session the record is removed from database if no new data is added.
        """
        self.cleared = True
        super().clear()

    def __setitem__(self, key, value):
        self.modified = True
        super().__setitem__(key, value)

    def abandon(self):
        """
        Immediately removes the session from the database.
        """
        self.cleared = True
        session_manager = create_session_manager(current_app)
        session_manager.clear(self.session_id)

    def create(self):
        """
        Creates a new session ID record.
        """
        self.clear()
        session_manager = create_session_manager(current_app)
        self.__dict__ = DynamoDbSession.create_session(session_manager).__dict__


class FlaskNullSessionInstance(DynamoDbSessionInstance):
    pass


class DynamoDbSession(SessionInterface):
    def open_session(self, app: Flask, request: Request) -> DynamoDbSessionInstance:
        session_manager = create_session_manager(app)
        failed = False
        if self._use_header(app):
            sid = request.cookies.get(self._cookie_name(app)) or request.headers.get(self._header_name(app))
        else:
            sid = request.cookies.get(self._cookie_name(app))

        if sid is not None:
            try:
                return session_manager.load(sid)
            except SessionError as exc:
                app.logger.warning(exc)
                failed = True

        instance = self.create_session(session_manager)
        if failed and sid is not None:
            instance.failed_sid = hashlib.sha512(sid.encode()).hexdigest()

        return instance

    @staticmethod
    def create_session(session_manager: SessionManager) -> DynamoDbSessionInstance:
        instance: DynamoDbSessionInstance = session_manager.create()
        instance.new = True
        return instance

    def save_session(self, app: Flask, session: SessionMixin, response: Response):
        """ Saves a session, depending on if it was used now or in the past.

        A session is `new` if a record was not found during `open_session`. We only save if it was also modified.

        Sessions that are not new are always saved, in order to update expiration. Accessing a session always updates
        expiration, regardless of whether or not it was saved.

        new    | modified | Saved?
        -------|----------|--------
        False  | False    | True
        False  | True     | True
        True   | False    | False
        True   | True     | True
        """
        # The actual type we need is DynamoDbSessionInstance
        session_instance = cast(DynamoDbSessionInstance, session)
        session_manager = create_session_manager(app)

        if session_instance.cleared:
            session_manager.clear(session_instance.session_id)
            name = self._cookie_name(app)
            domain = self.get_cookie_domain(app)
            path = self.get_cookie_path(app)
            response.delete_cookie(name, domain=domain, path=path)
            return

        if session_instance.modified or not session_instance.new:
            session_manager.save(session_instance)
            if self._use_header(app):
                response.headers[self._header_name(app)] = session_instance.session_id
                self._save_cookie(session_instance, app, response)
            else:
                self._save_cookie(session_instance, app, response)

    def _save_cookie(self, session_instance: DynamoDbSessionInstance, app: Flask, response: Response):
        name = self._cookie_name(app)
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        http_only = self.get_cookie_httponly(app)
        secure = self._cookie_secure(app)
        same_site = self._cookie_samesite(app)

        idle_expiration = session_instance.idle_timeout_seconds + current_timestamp()
        absolute_expiration = session_instance.absolute_timeout_seconds + int(session_instance.created.timestamp())
        expires = min(idle_expiration, absolute_expiration)

        response.set_cookie(name,
                            session_instance.session_id,
                            expires=expires,
                            secure=secure,
                            httponly=http_only,
                            samesite=same_site,
                            domain=domain,
                            path=path)

    @staticmethod
    def _use_header(app: Flask) -> bool:
        return app.config.get('SESSION_DYNAMODB_USE_HEADER', False)

    @staticmethod
    def _header_name(app: Flask) -> str:
        return app.config.get('SESSION_DYNAMODB_HEADER_NAME', 'x-id')

    def _cookie_name(self, app: Flask) -> str:
        if not app.config.get('SESSION_DYNAMODB_OVERRIDE_COOKIE_NAME', True):
            return self.get_cookie_name(app)
        return DEFAULT_COOKIE_NAME

    def _cookie_secure(self, app: Flask) -> bool:
        if not app.config.get('SESSION_DYNAMODB_OVERRIDE_COOKIE_SECURE', True):
            return self.get_cookie_secure(app)
        return DEFAULT_COOKIE_SECURE

    def _cookie_samesite(self, app: Flask) -> str:
        return DEFAULT_COOKIE_SAMESITE if self.get_cookie_samesite(app) is None else self.get_cookie_samesite(app)
