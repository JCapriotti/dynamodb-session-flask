from flask import Flask
from flask.sessions import SessionInterface, SessionMixin
from flask.wrappers import Request, Response

from ._session import DynamoDbSessionInstance

__all__ = ['TestSession']


class TestSession(SessionInterface):
    class TestInstance(DynamoDbSessionInstance):
        def abandon(self):
            """ Clears the session but doesn't do any DynamoDB actions """
            self.clear()

        def save(self):
            """ Mocked save method """

    def __init__(self):
        self.memory_instance = TestSession.TestInstance()

    def open_session(self, app: Flask, request: Request) -> DynamoDbSessionInstance:
        return self.memory_instance

    def save_session(self, app: Flask, session: SessionMixin, response: Response):
        return
