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
        self.sock.setsockopt(zmq.LINGER, 100)
        logger.info("Connecting to ZMQ peer at {0}".format(self.url))
        self.sock.connect(self.url)

    async def cleanup(self):
        self.sock.close()
        logger.info("Closed ZMQ socket")
        self.ctx.term()
        logger.info("Terminated ZMQ context")

    async def _process(self, data):
        self.sock.send_json(data)
