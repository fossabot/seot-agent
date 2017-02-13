import logging

import zmq
import zmq.asyncio

from . import BaseSource
from ..dpp import decode

logger = logging.getLogger(__name__)


class ZMQSource(BaseSource):
    def __init__(self, url="tcp://0.0.0.0:51423", **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.ctx = zmq.asyncio.Context()

    async def startup(self):
        self.sock = self.ctx.socket(zmq.PULL)
        logger.info("ZMQ listening at {0}".format(self.url))
        self.sock.bind(self.url)

    async def _run(self):
        while True:
            data = await self.sock.recv()
            await self._emit(decode(data))
