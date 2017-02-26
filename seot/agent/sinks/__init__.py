import asyncio
from abc import abstractmethod
from logging import getLogger

from .. import dpp
from ..node import Node

logger = getLogger(__name__)


class BaseSink(Node):
    def __init__(self, qsize=0, **kwargs):
        super().__init__(**kwargs)
        self._queue = asyncio.Queue(maxsize=qsize, loop=self.loop)

    async def write(self, data):
        logger.debug("Node {0} of type {1} received:\n{2}".format(
            self.name,
            self.__class__.__name__,
            dpp.format(data))
        )

        await self._queue.put(data)

    @abstractmethod
    async def _process(self, data):
        pass

    async def _run(self):
        while True:
            input_data = await self._queue.get()
            await self._process(input_data)
