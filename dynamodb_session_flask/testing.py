from flask import Flask
from flask.sessions import SessionInterface, SessionMixin
from flask.wrappers import Request, Response

from ._session import DynamoDbSessionInstance

__all__ = ['TestSession']


class TestSession(SessionInterface):
    memory_instance = DynamoDbSessionInstance()

    def open_session(self, app: Flask, request: Request) -> DynamoDbSessionInstance:
        return self.memory_instance

    def save_session(self, app: Flask, session: SessionMixin, response: Response):
        return
