import asyncio

import tornado.web

from waterbutler import exceptions
from waterbutler import settings
from waterbutler.identity import get_identity
from waterbutler.providers import core


def list_or_value(value):
    assert isinstance(value, list)
    if len(value) == 0:
        return None
    if len(value) == 1:
        return value[0].decode('utf-8')
    return [item.decode('utf-8') for item in value]


class BaseHandler(tornado.web.RequestHandler):

    ACTION_MAP = {}

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')

    @asyncio.coroutine
    def prepare(self):
        self.arguments = {
            key: list_or_value(value)
            for key, value in self.request.query_arguments.items()
        }
        self.arguments['action'] = self.ACTION_MAP[self.request.method]

        self.payload = yield from get_identity(settings.IDENTITY_METHOD, **self.arguments)

        self.provider = core.make_provider(
            self.arguments['provider'],
            self.payload['auth'],
            self.payload['credentials'],
            self.payload['settings'],
        )

    def write_error(self, status_code, exc_info):
        etype, exc, _ = exc_info
        if etype is exceptions.WaterButlerError:
            if exc.data:
                self.finish(exc.data)
                return

        self.finish({
            "code": status_code,
            "message": self._reason,
        })
