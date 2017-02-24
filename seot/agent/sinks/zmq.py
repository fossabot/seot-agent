import logging

import zmq
import zmq.asyncio

from . import BaseSink
from ..dpp import encode

logger = logging.getLogger(__name__)


class ZMQSink(BaseSink):
    def __init__(self, url="tcp://127.0.0.1:51423", linger=100, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.linger = linger
        self.ctx = zmq.asyncio.Context()

    async def startup(self):
        self.sock = self.ctx.socket(zmq.PUSH, io_loop=self.loop)
        self.sock.setsockopt(zmq.LINGER, self.linger)
        logger.info("Connecting to ZMQ peer at {0}".format(self.url))
        self.sock.connect(self.url)
        logger.info("Connected to ZMQ peer at {0}".format(self.url))

    async def cleanup(self):
        self.sock.close()
        logger.info("Closed ZMQ socket")
        self.ctx.term()
        logger.info("Terminated ZMQ context")

    async def _process(self, msg):
        self.sock.send(encode(msg))

    @classmethod
    def can_run(cls):
        return True
