import logging

import msgpack
import zmq
import zmq.asyncio

from . import BaseSource

logger = logging.getLogger(__name__)


class ZMQSource(BaseSource):
    def __init__(self, url, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.ctx = zmq.asyncio.Context()

    async def startup(self):
        self.sock = self.ctx.socket(zmq.PULL)
        self.sock.bind(self.url)

    async def _run(self):
        while True:
            msg = await self.sock.recv_json()
            await self._emit(msg)
