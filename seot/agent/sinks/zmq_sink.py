import collections
import logging

import msgpack
import zmq
import zmq.asyncio

from . import BaseSink

logger = logging.getLogger(__name__)


class ZMQSink(BaseSink):
    def __init__(self, url="tcp://127.0.0.1:51423", linger=100, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.linger = linger
        self.ctx = zmq.asyncio.Context()

    async def startup(self):
        self.sock = self.ctx.socket(zmq.PUSH)
        self.sock.setsockopt(zmq.LINGER, self.linger)
        logger.info("Connecting to ZMQ peer at {0}".format(self.url))
        self.sock.connect(self.url)

    async def cleanup(self):
        self.sock.close()
        logger.info("Closed ZMQ socket")
        self.ctx.term()
        logger.info("Terminated ZMQ context")

    def _encode(self, data):
        if isinstance(data, str):
            return data.encode("utf-8")
        elif isinstance(data, collections.Mapping):
            return dict(map(self._encode, data.items()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self._encode, data))
        else:
            return data

    async def _process(self, msg):
        data = msgpack.packb(self._encode(msg))
        self.sock.send(data)
