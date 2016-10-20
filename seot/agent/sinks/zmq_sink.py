import logging

import zmq
import zmq.asyncio

from . import BaseSink

logger = logging.getLogger(__name__)


class ZMQSink(BaseSink):
    def __init__(self, url, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.ctx = zmq.asyncio.Context()

    async def startup(self):
        self.sock = self.ctx.socket(zmq.PUSH)
        self.sock.connect(self.url)

    async def _process(self, data):
        self.sock.send_json(data)
