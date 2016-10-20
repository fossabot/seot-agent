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
    def __init__(self, level=logging.INFO, **kwargs):
        super().__init__(**kwargs)
        self.level = level

    async def _process(self, data):
        logger.log(self.level, "{0} received: {1}".format(self.name, data))


class NullSink(BaseSink):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _process(self, data):
        pass
