import asyncio

from ..dataflow import Node
from ..sinks import BaseSink


class BaseSource(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._next_nodes = []

    def connect(self, node):
        if not isinstance(node, BaseSink):
            raise ValueError("Expected a sink")

        self._next_nodes.append(node)

        return node

    async def _emit(self, data):
        await asyncio.wait([node.write(data) for node in self._next_nodes],
                           loop=self.loop)

    def next_nodes(self):
        return self._next_nodes


class ConstSource(BaseSource):
    def __init__(self, const, interval, **kwargs):
        super().__init__(**kwargs)
        self.const = const
        self.interval = interval

    async def _run(self):
        while True:
            await self._emit(self.const)
            await asyncio.sleep(self.interval)
