import asyncio
from abc import abstractmethod

from ..node import Node


class BaseSink(Node):
    def __init__(self, qsize=0, **kwargs):
        super().__init__(**kwargs)
        self._queue = asyncio.Queue(maxsize=qsize, loop=self.loop)

    async def write(self, data):
        await self._queue.put(data)

    @abstractmethod
    async def _process(self, data):
        pass

    async def _run(self):
        while True:
            input_data = await self._queue.get()
            await self._process(input_data)
