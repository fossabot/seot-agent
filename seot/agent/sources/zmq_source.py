import collections
import logging

import msgpack
import zmq
import zmq.asyncio

from . import BaseSource

logger = logging.getLogger(__name__)


class ZMQSource(BaseSource):
    def __init__(self, url="tcp://127.0.0.1:51423", **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.ctx = zmq.asyncio.Context()

    async def startup(self):
        self.sock = self.ctx.socket(zmq.PULL)
        logger.info("ZMQ listening at {0}".format(self.url))
        self.sock.bind(self.url)

    def _decode(self, data):
        if isinstance(data, bytes):
            return data.decode("utf-8")
        elif isinstance(data, collections.Mapping):
            return dict(map(self._decode, data.items()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self._decode, data))
        else:
            return data

    async def _run(self):
        while True:
            data = await self.sock.recv()
            msg = self._decode(msgpack.unpackb(data))
            await self._emit(msg)
