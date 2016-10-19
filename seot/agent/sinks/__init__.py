import asyncio
import logging
from abc import abstractmethod

from ..dataflow import Node

logger = logging.getLogger(__name__)


class BaseSink(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._queue = asyncio.Queue(loop=self.loop)

    async def write(self, data):
        await self._queue.put(data)

    @abstractmethod
    async def _process(self, data):
        pass

    async def _run(self):
        while True:
            input_data = await self._queue.get()
            await self._process(input_data)
            self._queue.task_done()


class DebugSink(BaseSink):
    async def _process(self, data):
        logger.debug(data)
